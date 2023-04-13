import re
import pytz

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class UserListAllSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 'fleet_id', 'is_online', 'status']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ajoute les informations supplémentaires à retourner dans la réponse
        # Si l'utilisateur est un rider, on renvoie la liste des courses qu'il a effectuées
        if instance.user_type == 'rider':
            ret['completed_rides'] = instance.rides.filter(status='completed').count()
            ret['cancelled_rides'] = instance.rides.filter(status='cancelled').count()
        # Si l'utilisateur est un driver, on renvoie la liste des courses qu'il a effectuées et son taux de satisfaction
        elif instance.user_type == 'driver':
            ret['completed_rides'] = instance.rides.filter(status='completed').count()
            ret['cancelled_rides'] = instance.rides.filter(status='cancelled').count()
            ret['satisfaction_rate'] = instance.driver_profile.satisfaction_rate
        return ret

class UserSerializer(serializers.ModelSerializer):
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
            'address', 'user_type', 'status',
        )
        extra_kwargs = {
            'email': {'read_only': True},
        }
        read_only_fields = (
            'id', 'full_name', 'age', 'remember_token', 'user_type', 'status',
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
            user_type='staff',
            status='pending',
            is_staff=True,
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


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_old_password(self, value):
        user = self.get_user()
        if not user.check_password(value):
            raise serializers.ValidationError(_('Invalid password'))
        return value

    def validate(self, data):
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError(_('New password cannot be same as old password'))
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(_('Passwords do not match'))
        return data

    def save(self, **kwargs):
        user = self.get_user()
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

    def get_user(self):
        return self.context['request'].user




