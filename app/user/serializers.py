from pytz import timezone

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, permissions

from core.models import UserBankAccounts, UserDetail, Wallet


User = get_user_model()


class UserBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBankAccounts
        fields = '__all__'

        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'user': {'write_only': True},
            'bank_name': {'required': True},
            'bank_code': {'required': True},
            'account_holder_name': {'required': True},
            'account_number': {'required': True},
        }

    def validate(self, attrs):
        bank_name = attrs.get('bank_name')
        bank_code = attrs.get('bank_code')
        account_holder_name = attrs.get('account_holder_name')
        account_number = attrs.get('account_number')

        if not bank_name:
            raise serializers.ValidationError(_('Bank name is required.'))

        if not bank_code:
            raise serializers.ValidationError(_('Bank code is required.'))

        if not account_holder_name:
            raise serializers.ValidationError(_('Account holder name is required.'))

        if not account_number:
            raise serializers.ValidationError(_('Account number is required.'))

        # Add additional validation logic here, if needed

        return attrs


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'user': {'write_only': True},
            'total_amount': {'required': True},
            'online_received': {'required': True},
            'manual_received': {'required': True},
            'total_withdrawn': {'required': True},
        }

    def validate(self, data):
        if data.get('total_amount', None) is not None and data['total_amount'] < 0:
            raise serializers.ValidationError(_("The total amount cannot be negative."))
        if data.get('online_received', None) is not None and data['online_received'] < 0:
            raise serializers.ValidationError(_("The online received payments cannot be negative."))
        if data.get('collected_cash', None) is not None and data['collected_cash'] < 0:
            raise serializers.ValidationError(_("The collected cash payments cannot be negative."))
        if data.get('manual_received', None) is not None and data['manual_received'] < 0:
            raise serializers.ValidationError(_("The manual received payments cannot be negative."))
        if data.get('total_withdrawn', None) is not None and data['total_withdrawn'] < 0:
            raise serializers.ValidationError(_("The total withdrawn amount cannot be negative."))
        return data

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]


class UserDetailSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserDetail
        fields = '__all__'


class RestrictedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'uid', 'user_type', 'status', 'fcm_token',
            'souvenir_token', 'email_verified_at', 'is_online',
            'last_notification_seen', 'is_available', 'is_verified_driver',
            'login_type', 'latitude', 'longitude',
            'last_location_update_at', 'fleet_id', 'player_id',
            'service_id', 'is_staff', 'is_active',
        )


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=5)

    class Meta:
        model = User
        fields = (
            'email', 'password', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'gender', 'address',
            'profile_image', 'timezone', 'age', 'full_name',
        )
        extra_kwargs = {
            'status': {'required': False},
            'email': {'validators': []},
            'password': {'write_only': True},
            'last_login': {'read_only': True},
            'email_verified_at': {'read_only': True},
            'player_id': {'read_only': True},
        }
        read_only_fields = ('full_name', 'age')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        if request and request.user.is_superuser:
            restricted_representation = RestrictedUserSerializer(instance).data
            representation.update(restricted_representation)
        return representation

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("A user with this email address already exists."))
        return value

    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate_date_of_birth(self, value):
        if value and (timezone.now().date() - value).days < 365.25 * 18:
            raise serializers.ValidationError("Users must be at least 18 years old.")
        return value

    def validate_latitude(self, value):
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Invalid latitude value. It must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Invalid longitude value. It must be between -180 and 180.")
        return value
