from cloudinary import CloudinaryImage
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save

from authors.apps.core.models import TimeStampModel


class Profile(TimeStampModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(
        'first name', max_length=30, blank=True, null=True)
    last_name = models.CharField(
        'last name', max_length=30, blank=True, null=True)
    birth_date = models.DateField('last name', null=True, blank=True)
    bio = models.TextField('bio', default='', null=True, blank=True)
    city = models.CharField('city', blank=True, null=True,
                            max_length=100, default='')
    country = models.CharField('country', blank=True,
                               null=True, max_length=100, default='')
    phone = models.IntegerField('phone', blank=True, null=True, default=0)
    website = models.URLField('website', blank=True, null=True, default='')
    image = CloudinaryField(
        'image',
        default="image/upload/t_media_lib_thumb/v1554230107/samples/people/boy-snow-hoodie.jpg")
    # Add a follows field to allow users to follow each other
    # symmetrical is False as if a user follows you,
    # then that does not automatically mean that you follow that user
    # related name for the user QuerySet filters 'followed_by'
    follows = models.ManyToManyField('Profile',
                                     through='CustomFollows',
                                     through_fields=(
                                         'from_profile', 'to_profile'),
                                     related_name="followed_by",
                                     symmetrical=False)

    def __str__(self):
        return self.user.username

    @property
    def get_username(self):
        return self.user.username

    @property
    def get_cloudinary_url(self):
        image_url = CloudinaryImage(str(self.image)).build_url(
            width=400, height=400, crop='fill')
        return image_url

    @property
    def followers(self):
        profiles = self.to_profile.all()
        return [profile.from_profile.user for profile in profiles]


"""
Signal receiver for 'post_save' signal sent by User model upon saving
"""


def create_profile(sender, **kwargs):
    if kwargs.get('created'):
        user_profile = Profile(user=kwargs.get('instance'))
        user_profile.save()


# connect the signal to the handler function
post_save.connect(create_profile, sender=settings.AUTH_USER_MODEL)


class CustomFollows(models.Model):
    from_profile = models.ForeignKey(Profile, on_delete=models.CASCADE,
                                     related_name="from_profile")
    to_profile = models.ForeignKey(Profile, on_delete=models.CASCADE,
                                   related_name="to_profile")
