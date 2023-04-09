from django.db import IntegrityError
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser
)

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

        except IntegrityError as e:
            return Response({
                'status': 'error',
                'message': 'User with this email or username already exists.',
                'error': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': _('Something went wrong.'),
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteUserAccount(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password', None)

        if not password:
            return Response(
                {'error': _('Please provide your password.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        authenticated_user = authenticate(username=user.username, password=password)
        if authenticated_user is None:
            raise AuthenticationFailed(_('Invalid password.'))

        # Delete the user's account and all associated data
        user.delete()
        return Response(
            {'message': _('Your account has been deleted.')},
            status=status.HTTP_204_NO_CONTENT
        )
