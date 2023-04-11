from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
)

from driver.serializers import DriverSerializer


User = get_user_model()


class DriverRegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = DriverSerializer

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
