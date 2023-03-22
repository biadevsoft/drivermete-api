from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
        EMAIL = 'email', _('Email')
        FACEBOOK = 'facebook', _('Facebook')
        GOOGLE = 'google', _('Google')
        TWITTER = 'twitter', _('Twitter')
    
    uid = models.CharField(_('uid'), max_length=255, null=True, blank=True)
    email = models.EmailField(_('email address'), max_length=70, unique=True)
    username = models.CharField(_('username'),max_length=30, unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    phone_number = models.CharField(_('phone'), null=True, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=10, choices=GenderUnitChoices.choices, null=True, blank=True)
    address = models.TextField(_('address'), max_length=255, blank=True, null=True)
    user_type = models.CharField(_('user type'), choices=UserTypeChoices.choices, max_length=10, default='rider')
    status = models.CharField(_('status'), max_length=20, choices=StatusUnitChoices.choices, default='pending')

    fcm_token = models.CharField(_('fcm token'), max_length=255, null=True, blank=True)
    remember_token = models.CharField(_('remember token'), max_length=100, null=True, blank=True)

    timezone = models.CharField(_('timezone'), max_length=5, default='UTC')
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

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

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
