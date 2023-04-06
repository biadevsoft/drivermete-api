from pytz import timezone

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, permissions

from core.models import UserBankAccount, UserDetail, Wallet


User = get_user_model()


class UserBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBankAccount
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


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'username', 'first_name',
            'last_name', 'phone_number', 'date_of_birth',
            'gender', 'address', 'profile_image', 'timezone',
            'user_type', 'status', 'login_type',
        )
        extra_kwargs = {
            'email': {'validators': []},
            'password': {'write_only': True},           
        }
        read_only_fields = (
            'id', 'full_name', 'age', 'remember_token', 
            'user_type', 'status', 'login_type',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            user_type='rider',
            status='pending',
            **validated_data
        )
        return user

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
