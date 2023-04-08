from django.contrib.auth import get_user_model

from rest_framework import serializers

User = get_user_model()


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
