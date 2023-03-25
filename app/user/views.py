from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model

from rest_framework.response import Response
from rest_framework import generics, status, permissions

from core.models import UserDetail, UserBankAccounts
from user.tasks import send_activation_email
from user.serializers import UserSerializer, UserDetailSerializer, UserBankAccountSerializer


User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user_type'] = User.UserTypeChoices.RIDER
        data['status'] = User.StatusUnitChoices.ACTIVE

        user_type = data.get('user_type')
        if user_type != 'rider':
            response_data = {
                'status': 'error',
                'message': 'User type must be "rider".',
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate activation token
        token_generator = default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Create activation URL
        activation_url = self.request.build_absolute_uri(
            reverse('user:activate-account', kwargs={'uidb64': uid, 'token': token})
        )

        # Send activation email
        send_activation_email.delay(user.email, activation_url)

        response_data = {
            'status': 'success',
            'message': 'User registered successfully.',
            'data': {
                'user': serializer.data
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class UserDriverRegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Create user
        user = User.objects.create(
            email=validated_data['email'],
            user_type='driver',
            is_active=False,
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create user detail
        user_detail = UserDetail(user=user)
        user_detail.save()

        # Create user bank account
        bank_account = UserBankAccounts(user=user)
        bank_account.save()

        # Generate activation token
        token_generator = default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Create activation URL
        activation_url = self.request.build_absolute_uri(
            reverse('user:activate-account', kwargs={'uidb64': uid, 'token': token})
        )

        # Send activation email
        send_activation_email.delay(user.email, activation_url)

        response_data = {
            'status': 'success',
            'message': 'Driver registered successfully.',
            'data': {
                'user': UserSerializer(user).data,
                'user_detail': UserDetailSerializer(user_detail).data,
                'bank_account': UserBankAccountSerializer(bank_account).data,
                'activation_url': activation_url
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class ActivateAccountView(generics.GenericAPIView):
    """Activate user account"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            if user.email_verified_at:
                return Response({'detail': 'Account already activated'})
            else:
                # Update email_verified_at field
                user.email_verified_at = timezone.now()
                user.save()
                return Response({'detail': 'Account activated successfully'})
        else:
            return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST)
