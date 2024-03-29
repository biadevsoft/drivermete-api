import os
import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)


def image_file_path(instance, filename):
    if isinstance(instance, User):
        prefix = 'user'
    else:
        prefix = 'document'

    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', prefix, filename)


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class UserTypeChoices(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        STAFF = 'staff', _('Staff')
        RIDER = 'rider', _('Rider')
        DRIVER = 'driver', _('Driver')

    class GenderUnitChoices(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')

    class StatusUnitChoices(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PENDING = 'pending', _('Pending')
        BANNED = 'banned', _('Banned')
        REJECT = 'reject', _('Reject')

    class LoginTypeChoices(models.TextChoices):
        MOBILE = 'mobile', _('mobile')
        EMAIL = 'email', _('Email')
        FACEBOOK = 'facebook', _('Facebook')
        GOOGLE = 'google', _('Google')
        TWITTER = 'twitter', _('Twitter')

    email = models.EmailField(_('email address'), max_length=70, unique=True)
    username = models.CharField(_('username'), max_length=50, unique=True, null=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    phone_number = models.CharField(_('phone'), max_length=17, unique=True, null=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=10, choices=GenderUnitChoices.choices, default='male')
    address = models.TextField(_('address'), max_length=255, blank=True, null=True)
    user_type = models.CharField(_('user type'), max_length=10, choices=UserTypeChoices.choices)
    status = models.CharField(_('status'), max_length=20, choices=StatusUnitChoices.choices)

    fcm_token = models.CharField(_('fcm token'), max_length=255, null=True, blank=True)
    remember_token = models.CharField(_('remember token'), max_length=100, null=True, blank=True)

    profile_image = models.ImageField(_('profile image'), null=True, upload_to=image_file_path)

    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    email_verified_at = models.DateTimeField(_('email verified at'), null=True, blank=True)
    last_notification_seen = models.DateTimeField(_('last notification seen'), blank=True, null=True)

    is_online = models.BooleanField(_('is online'), default=False)
    is_available = models.BooleanField(_('is available'), default=False)
    is_verified_driver = models.BooleanField(_('verified driver'), default=False)
    login_type = models.CharField(_('login type'), max_length=20, choices=LoginTypeChoices.choices, default='email')

    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    last_location_update_at = models.DateTimeField(_('last location update'), auto_now_add=True, null=True, blank=True)

    fleet_id = models.PositiveBigIntegerField(_('fleet id'), blank=True, null=True)
    player_id = models.CharField(_('player id'), max_length=255, blank=True, null=True)
    service_id = models.PositiveBigIntegerField(_('service id'), blank=True, null=True)

    is_staff = models.BooleanField(_('staff'), default=False)
    is_active = models.BooleanField(_('active'), default=True)

    created_at = models.DateTimeField(_('created at'), auto_now=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'user_type']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    @property
    def token(self):
        return self.auth_token.key

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.date_of_birth is None:
            return None
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year

        if (today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day)):
            age -= 1
        return age


class UserDetail(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_userdetail')
    car_model = models.CharField(_('car model'), max_length=50, blank=True, null=True)
    car_color = models.CharField(_('car color'), max_length=50, blank=True, null=True)
    car_plate_number = models.CharField(_('car plate number'), max_length=20, blank=True, null=True)
    car_production_year = models.CharField(_('car production year'), max_length=4, blank=True, null=True)
    work_address = models.TextField(_('work address'), blank=True, null=True)
    home_address = models.TextField(_('home address'), blank=True, null=True)
    work_latitude = models.DecimalField(_('work latitude'), blank=True, null=True, max_digits=9, decimal_places=6)
    work_longitude = models.DecimalField(_('work longitude'), blank=True, null=True, max_digits=9, decimal_places=6)
    home_latitude = models.DecimalField(_('home latitude'), blank=True, null=True, max_digits=9, decimal_places=6)
    home_longitude = models.DecimalField(_('home longitude'), blank=True, null=True, max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user detail')
        verbose_name_plural = _('user details')

    def __str__(self):
        return self.car_model if self.car_model else f"UserDetail {self.id}"


class UserBankAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_userbankaccount')
    bank_name = models.CharField(_('bank name'), max_length=30, blank=True, null=True)
    bank_code = models.CharField(_('bank code'), max_length=40, blank=True, null=True)
    account_holder_name = models.CharField(_('account holder name'), max_length=70, blank=True, null=True)
    account_number = models.CharField(_('account number'), max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(_('created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated'), blank=True, null=True)

    class Meta:
        verbose_name = _('user bank account')
        verbose_name_plural = _('user bank accounts')

    def __str__(self):
        return self.bank_name or ''


class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_wallet')
    total_amount = models.FloatField(_('total amount'), blank=True, null=True)
    online_received = models.FloatField(_('online received'), blank=True, null=True)
    collected_cash = models.FloatField(_('collected cash'), blank=True, null=True)
    manual_received = models.FloatField(_('manual received'), blank=True, null=True)
    total_withdrawn = models.FloatField(_('total withdrawn'), blank=True, null=True)
    currency = models.CharField(_('currency'), max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')

    def __str__(self):
        return f"Wallet of {self.user}"


class Roles(models.Model):
    name = models.CharField(_('name'), max_length=30, blank=True, null=True)
    guard_name = models.CharField(_('guard name'), max_length=30, blank=True, null=True)
    status = models.IntegerField(_('status'), blank=True, null=True)
    created_at = models.DateTimeField(_('created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated'), blank=True, null=True)

    class Meta:
        verbose_name = _('roles')
        verbose_name_plural = _('roles')

    def __str__(self):
        return self.name


class Document(models.Model):
    name = models.CharField(_('name'), max_length=30, blank=True, null=True)
    type = models.CharField(_('type'), max_length=30, default='driver')
    is_required = models.BooleanField(_('is required'), default=False)
    has_expiry_date = models.BooleanField(_('has expiry date'), default=False)
    status = models.IntegerField(_('status'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), blank=True, null=True)

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')

    def __str__(self):
        return self.name


class DriverDocument(models.Model):
    document_id = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='document_id_driverdocument')
    driver_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_id_driverdocument')
    expire_date = models.DateField(_('expiry date'), blank=True, null=True)
    is_verified = models.BooleanField(_('is verified'), default=False)
    document_image = models.ImageField(_('document image'), null=True, upload_to=image_file_path)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), blank=True, null=True)

    class Meta:
        verbose_name = _('driver document')
        verbose_name_plural = _('driver document')


class Regions(models.Model):

    class DistanceUnitChoices(models.TextChoices):
        KM = 'km', _('Km')
        MILE = 'mile', _('Mile')

    name = models.CharField(_('name'), max_length=30, null=True)
    distance_unit = models.CharField(_('distance unit'), choices=DistanceUnitChoices.choices, max_length=5, default=DistanceUnitChoices.KM)
    coordinates = models.CharField(_('coordinates'), max_length=100, blank=True, null=True)
    status = models.IntegerField(_('status'), default=1)
    timezone = models.CharField(_('timezone'), max_length=30, default='UTC')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), blank=True, null=True)

    class Meta:
        verbose_name = _('regions')
        verbose_name_plural = _('regions')

    def __str__(self):
        return self.name


class Sos(models.Model):

    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')

    region = models.ForeignKey(Regions, on_delete=models.CASCADE, related_name='region_sos')
    title = models.CharField(_('title'), max_length=255, blank=True, null=True)
    contact_number = models.CharField(_('contact number'), max_length=17, blank=True, null=True)
    status = models.CharField(_('status'), max_length=9, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), blank=True, null=True)

    class Meta:
        verbose_name = _('sos')
        verbose_name_plural = _('sos')

    def __str__(self):
        return f'{self.title} ({self.region})'
