from django import forms
from django.core.exceptions import ValidationError

from commonplace.models import Article, Video, Picture, Item, Category

class ArticleForm(forms.ModelForm):
    
    # fields: description, url, categories
    # generated: title, user, date created, fulltext.

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # Set URL read only if editing existing Article
        if instance is not None and instance.pk is not None:
            self.fields['url'].widget.attrs['readonly'] = True

        def clean_url(self):
            instance = getattr(self, 'instance', None)
            if instance is not None and instance.pk is not None:
                return instance.url
            else:
                return self.cleaned_data['url']

    url = forms.URLField(
        label='URL',
        required=True,
        )
    
    class Meta:
        model = Article
        exclude = ['creation_date', 'user', 'title', 'fulltext']

class PictureForm(forms.ModelForm):
    
    # fields: description, url, categories
    # generated: title, user, date created, thumbnail.

    def __init__(self, *args, **kwargs):
        super(PictureForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # Set URL read only if editing existing Picture
        if instance is not None and instance.pk is not None:
            self.fields['url'].widget.attrs['readonly'] = True

        def clean_url(self):
            instance = getattr(self, 'instance', None)
            if instance is not None and instance.pk is not None:
                return instance.url
            else:
                return self.cleaned_data['url']

    url = forms.URLField(
        label='URL',
        required=True,
        )
    
    class Meta:
        model = Picture
        exclude = ['creation_date', 'user', 'thumbnail']

class VideoForm(forms.ModelForm):
    
    # fields: description, url, categories
    # generated: title, user, date created, thumbnail.

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # Set URL read only if editing existing Video
        if instance is not None and instance.pk is not None:
            self.fields['url'].widget.attrs['readonly'] = True

        def clean_url(self):
            instance = getattr(self, 'instance', None)
            if instance is not None and instance.pk is not None:
                return instance.url
            else:
                return self.cleaned_data['url']

    url = forms.URLField(
        label='URL',
        required=True,
        )
    
    class Meta:
        model = Video
        exclude = ['creation_date', 'user', 'screenshot']


class AddCategory(forms.ModelForm):
    
    def __init__(self,*args, **kwargs):
        super(AddCategory,self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
    class Meta:
        model = Category