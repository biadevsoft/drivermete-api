from django.db import IntegrityError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from app.utils.custom_pagination import CustomPagination
from user.serializers import UserSerializer, ChangePasswordSerializer, UserListAllSerializer


User = get_user_model()


class UserListAllView(APIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = [UserListAllSerializer]
    pagination_class = CustomPagination()
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user

        if not user.is_superuser and not user.is_staff:
            raise PermissionDenied(_('You are not authorized to access this resource.'))

        user_type = self.request.query_params.get('user_type', 'rider')
        fleet_id = self.request.query_params.get('fleet_id', None)
        is_online = self.request.query_params.get('is_online', None)
        status = self.request.query_params.get('status', None)

        queryset = User.objects.all()

        if user.is_staff:
            if user_type not in ['rider', 'driver']:
                raise PermissionDenied(_('You are not authorized to access this resource.'))

            fleet = user.is_staff
            if not fleet:
                return queryset.none()


        if user_type:
            queryset = queryset.filter(user_type=user_type)
        if fleet_id:
            queryset = queryset.filter(fleet_id=fleet_id)
        if is_online is not None:
            queryset = queryset.filter(is_online=is_online)
        if status is not None:
            queryset = queryset.filter(status=status)

        per_page_param = self.request.query_params.get('per_page', None)
        if per_page_param is not None:
            try:
                per_page = int(per_page_param)
                if per_page == -1:
                    per_page = queryset.count()
                elif per_page < 1:
                    per_page = settings.REST_FRAMEWORK['PAGE_SIZE']
            except ValueError:
                per_page = settings.REST_FRAMEWORK['PAGE_SIZE']

        self.pagination_class.page_size = per_page

        return queryset.order_by('-id')

    def get(self, request):
        queryset = self.get_queryset()
        page = self.pagination_class.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.pagination_class.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class ManagerRegisterView(generics.CreateAPIView):
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
        

class UpdateUserStatus(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        new_status = request.data.get('status')
        user_type = user.user_type

        if not new_status:
            return Response({'error': 'Missing status parameter'}, status=status.HTTP_400_BAD_REQUEST)

        if user_type not in ['rider', 'driver']:
            raise PermissionDenied("You don't have permission to change status for this user type.")

        user.status = new_status
        user.save(update_fields=['status'])

        serializer = self.serializer_class(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

"""
class UserLogoutView(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
       
        try:
            refresh_token = request.data['refresh_token']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'error': 'Invalid token provided.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'User logged out successfully.'}, status=status.HTTP_200_OK)
"""

class UserPasswordChangeView(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not request.user.check_password(old_password):
            raise ValidationError({'old_password': ['Incorrect old password.']})

        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            raise ValidationError({'new_password': e})

        request.user.set_password(new_password)
        request.user.save()

        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
