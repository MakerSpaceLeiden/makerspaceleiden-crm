from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager 
from django.utils.translation import ugettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    # username = None
    email = models.EmailField(_('email address'), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    form_on_file = models.BooleanField( 
	default=False,
    )
    email_confirmed = models.BooleanField(
        default=False
    )
    history = HistoricalRecords()
    objects = UserManager() 
    def __str__(self):
        return self.first_name + ' ' + self.last_name + ' (' + self.username + ')'


class Tag(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=30)
    history = HistoricalRecords()

    def __str__(self):
        return self.tag + ' (' + self.owner.user.username + ')'

class PermitType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description =  models.CharField(max_length=200)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class Entitlement(models.Model):
    permit = models.ForeignKey(
	'PermitType',
	on_delete=models.CASCADE,
    )
    holder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='isGivenTo',
    )
    issuer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='isIssuedBy',
    )
    history = HistoricalRecords()

    def __str__(self):
        return str(self.holder) + ' on ' + self.permit.name
    def save_model(self, request, obj, form, change):
        if not obj.issuer:
            obj.issuer = request.user
        obj.save()

