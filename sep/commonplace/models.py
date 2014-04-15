from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    verbose_name_plural = 'Categories'
    name = models.CharField(max_length=200, unique=True)
    def __unicode__(self):
        return self.name

class Folder(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    def __unicode__(self):
        return self.name

class Item(models.Model):
    creation_date = models.DateTimeField('date created', auto_now_add=True)
    title = models.CharField(max_length=400)
    description = models.CharField(max_length=2000)
    url = models.URLField(max_length=2000, unique=True) # don't let two users submit same item
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    categories = models.ManyToManyField(Category, blank=True)
    folders = models.ManyToManyField(Folder, blank=True)
    def __unicode__(self):
        return self.title

class Article(Item):
    fulltext = models.TextField()

class Picture(Item):
    thumbnail = models.ImageField(upload_to='picture_thumbnails')

class Video(Item):
    screenshot = models.ImageField(upload_to='video_screenshots')

