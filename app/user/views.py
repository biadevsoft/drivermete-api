import jwt
import datetime

from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import exceptions
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed

from user.tasks import send_activation_email
from user.serializers import UserSerializer


User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            # Generate activation token
            token_generator = default_token_generator
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)

            # Create activation URL
            activation_url = request.build_absolute_uri(reverse('user:activate-account', kwargs={'uidb64': uid, 'token': token}))

            # Send activation email
            send_activation_email.delay(user.email, activation_url)

            response_data = {
                'status': 'success',
                'message': 'User registered successfully.',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e.detail),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Something went wrong.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ActivateAccountView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token): 
        try: 
            uid = force_str(urlsafe_base64_decode(uidb64)) 
            user = User.objects.get(pk=uid) 
        except (TypeError, ValueError, OverflowError, User.DoesNotExist): 
            return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST) 

        try: 
            if user.email_verified_at: 
                return Response({'detail': 'Account already activated'}) 

            if default_token_generator.check_token(user, token): 
                user.email_verified_at = timezone.now() 
                token_generator = default_token_generator 
                user.souvenir_token = token_generator.make_token(user) 
                user.save() 
                return Response({'detail': 'Account activated successfully'}) 

            return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST) 
        except Exception as e: 
            return Response({
                'status': 'error',
                'message': str(e.detail)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            raise exceptions.ValidationError('Both email and password are required fields.')

        user = authenticate(email=email, password=password)

        if not user:
            raise exceptions.AuthenticationFailed('User not found or incorrect password.')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        response = Response()
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {'jwt': token}
        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {'message': 'Successfully logged out.'}
        return response


class UserView(APIView):

    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithm=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)
