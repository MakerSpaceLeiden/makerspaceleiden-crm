from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy,reverse
from stdimage.models import StdImageField

from django.db.models.signals import pre_delete, pre_save
from stdimage.utils import pre_delete_delete_callback, pre_save_delete_callback

from makerspaceleiden.utils import upload_to_pattern

import re

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
    class Meta:
        ordering = ['first_name', 'last_name']

    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=40, blank=True, null=True, help_text="Optional; only visible to the trustees and board delegated administrators")

    image = StdImageField(upload_to=upload_to_pattern, variations=settings.IMG_VARIATIONS, validators=settings.IMG_VALIDATORS, blank=True, default='')

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
        return self.first_name + ' ' + self.last_name

    def name(self):
        return self.__str__()

    def path(self):
       return  reverse('overview', kwargs = { 'member_id' :  self.id })

    def url(self):
       return  settings.BASE + self.path()

class Tag(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=30, unique=True) #, editable = False)
    description = models.CharField(max_length=300, blank=True, null=True)

    last_used = models.DateTimeField(blank=True, null = True) # , editable = False)

    history = HistoricalRecords()

    def __str__(self):
        return self.tag + ' (' + str(self.owner) + ')'

def clean_tag_string(tag):
    try:
       return  '-'.join([ b for b in re.compile('[^0-9]+').split(tag.upper()) 
           if b is not None and b is not '' and int(b) >=0 and int(b) < 256])
    except ValueError as e:
       pass

    return None

# Handle image cleanup.
pre_delete.connect(pre_delete_delete_callback, sender=User)
pre_save.connect(pre_save_delete_callback, sender=User)
