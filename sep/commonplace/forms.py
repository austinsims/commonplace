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

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            url = kwargs['instance'].url
        return super(ArticleForm, self).__init__(*args, **kwargs)
