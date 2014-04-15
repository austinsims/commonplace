from django import forms
from django.core.exceptions import ValidationError
from tinymce.widgets import TinyMCE

from commonplace.models import *
custom_widgets = {'folders' : forms.RadioSelect, 'categories' : forms.CheckboxSelectMultiple }

class ItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ItemForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        qs = Folder.objects.filter(user=user)
        self.fields['folders'].queryset = qs

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

class ArticleForm(ItemForm):    
    class Meta:
        model = Article
        exclude = ['creation_date', 'user', 'title']
        template = "commonplace/edit_item.html"
        widgets = {'fulltext' : TinyMCE(
            attrs={ 'cols': 120, 'rows':25 }, 
            mce_attrs={
                'theme' : 'advanced',
                'theme_advanced_buttons1' : "bold,italic,underline,strikethrough,|,fontsizeselect,backcolor",
            })
        }
        
class PictureForm(ItemForm):
    class Meta:
        model = Picture
        exclude = ['creation_date', 'user', 'thumbnail']

class VideoForm(ItemForm):
    class Meta:
        model = Video
        exclude = ['creation_date', 'user', 'screenshot']


class AddCategory(forms.ModelForm):
    
    def __init__(self,*args, **kwargs):
        super(AddCategory,self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
    class Meta:
        model = Category

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        exclude = ['user']
