from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.utils import timezone

from django.db.models import Q

from django.core.files.uploadedfile import SimpleUploadedFile

# For making thumbnails & screenshots
from PIL import Image, ImageOps
from cStringIO import StringIO
import gdata.youtube.service

# For making article summaries
from readability.readability import Document as ReadableDocument
import urllib

# various python imports
import re
import os
from collections import defaultdict

from commonplace.models import *
from commonplace.forms import *
from django.contrib.auth import get_user_model
User = get_user_model()


# Utility functions; these are not views.

def make_thumbnail(url, size):
    file = StringIO(urllib.urlopen(url).read())
    img = Image.open(file)
    if img.mode not in ("L", "RGB"):
        img = img.convert("RGB")
    img.thumbnail((256,256), Image.ANTIALIAS)
    return img

def process_new_categories(item,new_categories):
    for cname in new_categories.split(' '):
        if (len(cname) > 0):
            item.categories.get_or_create(name=cname)
    item.save()

# Commonplace views

# Front page view.
def index(request):
    
    # Only display content if the user has logged in.
    if not request.user.is_authenticated():
        return render(request, 'commonplace/index.html')
    
    # Generate list of latest items.
    latest_items = Item.objects.order_by('-creation_date')
    
    # Generate list of categories for which the user has submitted articles.
    recommended_categories = []
    for item in Item.objects.filter(user=request.user):
        recommended_categories.extend(item.categories.all())
    
    # Generate list of recommended items.
    recommended_items = []
    for item in Item.objects.filter(~Q(user=request.user)):
        if list(set(item.categories.all()) & set(recommended_categories)):
            recommended_items.append(item)
    
    # Return lists of latest and recommended items.
    return render(request, 'commonplace/index.html', {
        'latest_items' : latest_items[:10],
        'recommended_items' : recommended_items[:10],
    })

# Display user preferences page.
def user_preferences(request):
    folders = Folder.objects.filter(user=request.user)
    return render(request, 'commonplace/user_preferences.html', {'folders' : folders})

def my_items(request):
    results = Item.objects.filter(user=request.user)
    my_folders = Folder.objects.filter(user=request.user)
    my_items = defaultdict(list)
    
    # Sort items by folder.
    for item in results:
        if item.folders.count() > 0:
            # add to appropriate list
            for folder in item.folders.filter(user=request.user):
                my_items[folder.name].append(item)
        else:
            # add to 'loose_items' list
            my_items['loose_items'].append(item)

    context = { 
        'my_items' : dict(my_items),
        }
    return render(request, 'commonplace/my_items.html', context)

def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if request.user.pk is item.user.pk:
        if hasattr(item,'article'):
            article = get_object_or_404(Article, pk=pk)
            form = ArticleForm(request.POST or None, instance=article, user=request.user)
        elif hasattr(item,'picture'):
            picture = get_object_or_404(Picture, pk=pk)
            form = PictureForm(request.POST or None, instance=picture, user=request.user)
        elif hasattr(item,'video'):
            video = get_object_or_404(Video, pk=pk)
            form = VideoForm(request.POST or None, instance=video, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('my_items')
        return render(request, 'commonplace/edit_item.html', {'form' : form })
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to edit that!'})
    
# View items in a certain category
def items_by_category(request, category_name):
    try:
        cat = Category.objects.get(name=category_name)
        items = cat.item_set.all()
    except Category.DoesNotExist:
        raise Http404
    return render(request, 'commonplace/items_by_category.html', {
            'category' : cat,
            'items' : items,
            })

# View items by a certain user
def items_by_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
        items = user.item_set.all()
    except User.DoesNotExist:
        raise Http404
    return render(request, 'commonplace/items_by_user.html', {
            'user' : user,
            'items' : items,
            'something' : 'blah',
            })

# Item views

# used for index
class ItemListView(generic.ListView):
    model = Item

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

def item_detail(self, pk):
    item = get_object_or_404(Item, pk=pk)
    baseValues = { 
        'title' : item.title, 
        'categories' : item.categories, 
        'description' : item.description, 
        'url' : item.url,
        'author' : item.user,
        }

    if hasattr(item,'article'):
        article = Article.objects.get(pk=item.pk)
        specValues = {'fulltext' : article.fulltext }
    elif hasattr(item,'picture'):
        picture = Picture.objects.get(pk=item.pk)
        specValues = {'thumbnail' : picture.thumbnail }
    elif hasattr(item,'video'):
        video = Video.objects.get(pk=item.pk)
        specValues = {'screenshot' : video.screenshot }

    values = dict(baseValues.items() + specValues.items())
    return render(self, 'commonplace/item_detail.html', values)


def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.user.pk is item.user.pk:
        if request.method == 'POST':
            item.delete()
            return redirect('my_items')
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to delete that!'})
    return render(request, 'commonplace/item_confirm_delete.html', {'item' : item })

# Article views


def submit_article(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})

    if request.method == 'GET':
        form = ArticleForm(user=request.user)
    else:
        # POST request: handle form upload.
        form = ArticleForm(request.POST, user=request.user) # bind data from request

        # If data is valid, create article and redirect
        if form.is_valid():
            # Retrieve short title and readable text
            url = form.cleaned_data['url']
            try:
                html = urllib.urlopen(url).read()
            except IOError:
                return render(request, 'commonplace/error.html', {'message' : 'Sorry, the webpage at your URL %s does not exist!' % url})

            article = form.save(commit=False)


            doc = ReadableDocument(html)
            summary = doc.summary()
            summary = re.sub(r'</?html>','', summary)
            summary = re.sub(r'</?body>','', summary)
            article.title = doc.short_title()
            article.fulltext = summary
            article.user = request.user

            article.save()
            form.save_m2m()

            # Check for new categories from form
            new_categories = form.data.get('new_categories')
            if new_categories is not None:
                process_new_categories(article, new_categories)
            
            article.save()    

            

            return HttpResponseRedirect(reverse('item_detail', kwargs={'pk' : article.pk}))

    return render(request, 'commonplace/edit_item.html', {
                'form' : form,
                })

# Picture views

def submit_picture(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})
    else:
        if request.method == 'GET':
            form = PictureForm(user=request.user)
        else:
            # POST request: handle form upload.
            form = PictureForm(request.POST, user=request.user) # bind data from request

            # If data is valid, create article and redirect
            if form.is_valid():

                # Retrieve short title and readable text
                # TODO: Scan a webpage for images instead of requiring direct link to image.
                url = form.cleaned_data['url']
                try:
                    # TODO: Generate a thumbnail. May throw NotAPictureError
                    thumbnail = make_thumbnail(url, (256,256))
                except IOError: # caught if PIL couldn't load the thumbnail for whatever reason
                    # TODO: Make a template for this error message and render it
                    return render(request, 'commonplace/error.html', {'message' : 'Sorry, the picture at your URL %s does not exist!' % url})

                picture = form.save(commit=False)

                # Deal with the thumbnail
                temp_handle = StringIO()
                thumbnail.save(temp_handle, 'JPEG')
                temp_handle.seek(0)
                # Save image to a SimpleUploadedFile which can be saved into an ImageField
                suf = SimpleUploadedFile(os.path.split(url)[-1], temp_handle.read(), content_type='JPEG')
                picture.thumbnail = suf
                picture.user = request.user
                picture.save()
                form.save_m2m()

                # Check for new categories from form
                new_categories = form.data.get('new_categories')
                if new_categories is not None:
                    process_new_categories(picture,new_categories)

                return HttpResponseRedirect(reverse('item_detail', kwargs={'pk' : picture.pk}))

    return render(request, 'commonplace/edit_item.html', {
            'form' : form,
            })


# Video views

def submit_video(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})
    else:
        if request.method == 'GET':
            form = VideoForm(user=request.user)
        else:
            # POST request: handle form upload.
            form = VideoForm(request.POST, user=request.user) # bind data from request

            # If data is valid, create article and redirect
            if form.is_valid():

                # Retrieve short title and readable text
                # TODO: Scan a webpage for images instead of requiring direct link to image.
                url = form.cleaned_data['url']

                video = form.save(commit=False)

                # Save image to a SimpleUploadedFile which can be saved into an ImageField
                if 'youtube.com/watch?v=' in url:
                    video_id = url.split('?v=')[-1]
                    yt = gdata.youtube.service.YouTubeService()
                    entry = yt.GetYouTubeVideoEntry(video_id=video_id)
                    thumb_url = entry.media.thumbnail[0].url
                    screenshot = make_thumbnail(thumb_url, (256,256))
                    temp_handle = StringIO()
                    screenshot.save(temp_handle, 'JPEG')
                    temp_handle.seek(0)
                    suf = SimpleUploadedFile(os.path.split(url)[-1], temp_handle.read(), content_type='JPEG')
                    video.screenshot = suf
                video.user = request.user
                video.save()
                form.save_m2m()

                # Check for new categories from form
                new_categories = form.data.get('new_categories')
                if new_categories is not None:
                    process_new_categories(video, new_categories)

                return HttpResponseRedirect(reverse('item_detail', kwargs={'pk' : video.pk}))

    return render(request, 'commonplace/edit_item.html', {
            'form' : form,
            })

# View search results matching the specified search string.
def search_items(request):
    if request.method == 'POST':
        
        # Obtain user input for search string from POST data.
        search_string = request.POST.get('search_string')
        
        # Query for a list of matching items based on title or description.
        items_with_matching_title_or_description = Item.objects.filter(
            Q(title__icontains=search_string) |
            Q(description__icontains=search_string))
        
        # Query for a list of matching items (which are articles) based on fulltext.
        pk_list = []
        for article in Article.objects.filter(fulltext__icontains=search_string):
            pk_list.append(article.pk)
        items_with_matching_fulltext = Item.objects.filter(pk__in=pk_list)
            
        # Find union of the two querysets.
        items = items_with_matching_title_or_description | items_with_matching_fulltext
        
        # Return search results.    
        return render(request, 'commonplace/search_results.html', {
            'search_string' : search_string,
            'items' : items, })

# User views

def user_detail(request, pk):
    user = User.objects.get(pk=pk)
    ctx = { 'user' : user }
    return render(request, 'commonplace/user_detail.html', ctx)

# Add new categories

def test_picture(request,pk):
    picture = Picture.objects.get(pk=pk)
    test = {'picture' : picture}
    return render(request,'commonplace/index.html',test)


# Folder views

class FolderCreate(generic.CreateView):
    model = Folder
    form_class = FolderForm
    def form_valid(self, form):
        folder = form.save(commit=False)
        folder.user = self.request.user
        folder.save()
        return HttpResponseRedirect(reverse('user_preferences'))
