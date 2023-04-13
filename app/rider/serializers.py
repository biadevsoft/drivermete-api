import re
import pytz

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class RiderSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=6, style={'input_type': 'password'})
    phone_number = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'confirm_password',
            'username', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'gender',
            'address', 'profile_image', 'timezone',
            'user_type', 'status', 'login_type',
        )
        extra_kwargs = {
            'email': {'read_only': True},
        }
        read_only_fields = (
            'id', 'full_name', 'age', 'remember_token', 'user_type', 'status', 'login_type',
        )

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({'password': _('Passwords must match.')})

        first_name = data.get('first_name')
        if first_name:
            if len(first_name) < 3:
                raise serializers.ValidationError(_('First name must be at least 3 characters long.'))
            if not first_name.isalpha():
                raise serializers.ValidationError(_('First name must only contain alphabetical characters.'))

        last_name = data.get('last_name')
        if last_name:
            if len(last_name) < 3:
                raise serializers.ValidationError(_('Last name must be at least 3 characters long.'))
            if not last_name.isalpha():
                raise serializers.ValidationError(_('Last name must only contain alphabetical characters.'))

        gender = data.get('gender')
        if gender:
            if gender not in User.GenderUnitChoices.values:
                raise serializers.ValidationError(_('Invalid gender choice.'))

        profile_image = data.get('profile_image')
        if profile_image:
            # Check if the uploaded file is an image
            if not profile_image.content_type.startswith('image'):
                raise serializers.ValidationError(_('File must be an image.'))

            # Check if the image is too large
            if profile_image.size > (1024 * 1024):
                raise serializers.ValidationError(_('Image file size must be under 1 MB.'))

            # Check if the image is too small
            if profile_image.width < 100 or profile_image.height < 100:
                raise serializers.ValidationError(_('Image dimensions must be at least 100x100 px.'))

        timezone_data = data.get('timezone')
        if timezone_data:
            try:
                timezone.activate(pytz.timezone(timezone_data))
                timezone.deactivate()
            except pytz.UnknownTimeZoneError:
                raise serializers.ValidationError(_('Invalid timezone choice.'))

        # convertir le format de phone_number
        phone_number = data['phone_number']
        match = re.match(r'^(\+\d{1,3})?[ -]?(\d{3})[ -]?(\d{3})[ -]?(\d{4})$', phone_number)
        if match:
            data['phone_number'] = '+{} {}-{}-{}'.format(match.group(1) or '1', match.group(2), match.group(3), match.group(4))
        else:
            raise serializers.ValidationError({'phone_number': _('Invalid phone number format.')})

        date_of_birth = data.get('date_of_birth')
        if date_of_birth:
            year = str(date_of_birth.year)
            if not year.startswith(('19', '20')):
                raise serializers.ValidationError(_("The year in date of birth must start with 19 or 20."))

        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': _('Email already exists')})

        user = User.objects.create_user(
            email=email,
            password=password,
            user_type='rider',
            status='pending',
            login_type='email',
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        if instance.email != validated_data.get('email', instance.email):
            if User.objects.filter(email=validated_data.get('email')).exists():
                raise serializers.ValidationError({'email': _('This email address is already in use.')})
        instance = super().update(instance, validated_data)
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        return instance


class MyTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError(_('Invalid email or password.'))

        if not user.check_password(password):
            raise serializers.ValidationError(_('Invalid email or password.'))

        if not user.is_active:
            raise serializers.ValidationError(_('This account is inactive.'))

        attrs['user'] = user
        return attrs

    def get_token(self, user):
        token = RefreshToken.for_user(user)
        user_data = RiderSerializer(user).data

        token['user'] = user_data
