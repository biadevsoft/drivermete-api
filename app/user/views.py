from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.utils.custom_pagination import CustomPagination
from user.serializers import AdminSerializer, ChangePasswordSerializer
from rider.serializers import UserSerializer
from driver.serializers import DriverSerializer


User = get_user_model()


class UserListView(generics.ListAPIView):
    serializer_class = AdminSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAdminUser)

    def get_queryset(self):
        user_type = self.request.query_params.get('user_type', 'rider')
        fleet_id = self.request.query_params.get('fleet_id', None)
        is_online = self.request.query_params.get('is_online', None)
        status = self.request.query_params.get('status', None)
        per_page = self.request.query_params.get('per_page', 10)

        user_list = User.objects.all()
        if user_type:
            user_list = user_list.filter(user_type=user_type)
        if fleet_id:
            user_list = user_list.filter(fleet_id=fleet_id)
        if is_online is not None:
            user_list = user_list.filter(is_online=is_online)
        if status is not None:
            user_list = user_list.filter(status=status)

        if per_page == '-1':
            per_page = user_list.count()

        self.pagination_class.page_size = int(per_page)
        return user_list

    def get_serializer_class(self):
        user_type = self.request.query_params.get('user_type', 'rider')
        return DriverSerializer if user_type == 'driver' else UserSerializer


class ManagerRegisterView(generics.CreateAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = AdminSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            response_data = {
                'status': 'success',
                'message': 'User registered successfully.',
                'data': {
                    'user': AdminSerializer(user, context={'request': request}).data,
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
    serializer_class = AdminSerializer
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


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        """
        Log out a user and delete their auth token.
        """
        try:
            refresh_token = request.data['refresh_token']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'error': 'Invalid token provided.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'User logged out successfully.'}, status=status.HTTP_200_OK)


class UserPasswordChangeView(APIView):
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

        serializer = AdminSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
