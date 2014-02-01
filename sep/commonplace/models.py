from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    verbose_name_plural = 'Categories'
    name = models.CharField(max_length=200)
    def __unicode__(self):
        return self.name

class Item(models.Model):
    creation_date = models.DateTimeField('date created')
    title = models.CharField(max_length=400)
    description = models.CharField(max_length=2000)
    url = models.CharField(max_length=2000)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    categories = models.ManyToManyField(Category)

class Article(Item):
    fulltext = models.CharField(max_length=4096)

class Picture(Item):
    thumbnail = models.ImageField(upload_to='picture_thumbnails')

class Video(Item):
    screenshot = models.ImageField(upload_to='video_screenshots')
