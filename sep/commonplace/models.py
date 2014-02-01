from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200)
    def __unicode__(self):
        return self.name

class Item(models.Model):
    creation_date = models.DateTimeField('date created')
    title = models.CharField(max_length=400)
    description = models.CharField(max_length=2000)
    url = models.CharField(max_length=2000)
    user = models.ForeignKey(User)
    categories = models.ManyToManyField(Category)

class Article(Item):
    fulltext = models.CharField(max_length=4096)
