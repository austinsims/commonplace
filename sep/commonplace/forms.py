from django import forms
from django.core.exceptions import ValidationError

from commonplace.models import Article, Video, Picture, Item, Category

class ArticleForm(forms.ModelForm):
    
    # fields: description, url, categories
    # generated: title, user, date created, fulltext.

    url = forms.URLField(
        label='URL',
        required=True,
        )
    
    class Meta:
        model = Article
        exclude = ['creation_date', 'user', 'title', 'fulltext']
