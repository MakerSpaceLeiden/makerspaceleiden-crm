from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager 
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy,reverse

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
    username = None
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

    def name(self):
        return __str__(self)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    def path(self):
       return  reverse('overview', kwargs = { 'member_id' :  self.id })

    def url():
       return  settings.BASE + self.path()

class Tag(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=30)
    history = HistoricalRecords()

    def __str__(self):
        return self.tag + ' (' + str(self.owner) + ')'

