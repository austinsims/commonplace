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
            new_cat = Category.objects.get_or_create(name=cname)[0]
            item.categories.add(new_cat)
            item.save()

# Convert a list of items to their specific inheritances (article, picture, or video).            
def inheritize_items(items):
    inheritized_items = []
    for item in items:
        if hasattr(item, 'article'):
            inheritized_items.append(get_object_or_404(Article, pk=item.pk))
        elif hasattr(item, 'picture'):
            inheritized_items.append(get_object_or_404(Picture, pk=item.pk))
        elif hasattr(item, 'video'):
            inheritized_items.append(get_object_or_404(Video, pk=item.pk))
    return inheritized_items

# Commonplace views

# Front page view.
def index(request):
    
    MAX_DISP_LATEST_ITEMS = 10
    MAX_DISP_REC_ITEMS = 10
    
    # Only display content if the user has logged in.
    if not request.user.is_authenticated():
        return render(request, 'commonplace/index.html')
    
    # Generate list of latest items.
    latest_items_raw = Item.objects.order_by('-creation_date')[:MAX_DISP_LATEST_ITEMS]
    latest_items = inheritize_items(latest_items_raw)
    
    # Generate list of categories for which the user has submitted articles.
    recommended_categories = []
    for item in Item.objects.filter(user=request.user):
        recommended_categories.extend(item.categories.all())
    
    # Generate list of recommended items.
    recommended_items_raw = []
    for item in Item.objects.filter(~Q(user=request.user)):
        if list(set(item.categories.all()) & set(recommended_categories)):
            recommended_items_raw.append(item)
    recommended_items_raw = recommended_items_raw[:MAX_DISP_REC_ITEMS]
    recommended_items = inheritize_items(recommended_items_raw)
    
    # Return lists of latest and recommended items.
    return render(request, 'commonplace/index.html', {
        'latest_items' : latest_items,
        'recommended_items' : recommended_items,
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

def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    baseValues = { 
        'title' : item.title, 
        'categories' : item.categories, 
        'description' : item.description, 
        'url' : item.url,
        'author' : item.user,
        'absolute_url' : request.build_absolute_uri(reverse('item_detail', args=[item.pk]))
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
    return render(request, 'commonplace/item_detail.html', values)


def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.user.pk is item.user.pk:
        if request.method == 'POST':
            item.delete()
            return redirect('my_items')
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to delete that!'})
    return render(request, 'commonplace/item_confirm_delete.html', {'item' : item })

def submit_item(request):
    if not request.user.is_authenticated():
        return render(
            request,
            'commonplace/error.html',
            { 'message' : 'You must log in to submit content.' }
        )
    
    if request.method == 'GET':
        
        # Determine the appropriate form to display based on the selected item type.
        item_type = request.GET.get('item_type')
        if item_type == 'picture':
            form = PictureForm(user=request.user)
        elif item_type == 'video':
            form = VideoForm(user=request.user)
        else:
            form = ArticleForm(user=request.user)
            
    else:
        
        # Determine the appropriate form to bind data from the request.
        item_type = request.POST.get('item_type')
        if item_type == 'article':
            form = ArticleForm(request.POST, user=request.user)
        elif item_type == 'picture':
            form = PictureForm(request.POST, user=request.user)
        else:
            form = VideoForm(request.POST, user=request.user)
        
        # If the form data is valid, save the data for the item.
        if form.is_valid():
            url = form.cleaned_data['url']
            
            # Perform logic for articles.
            if item_type == 'article':
                
                # Validate URL.
                try:
                    html = urllib.urlopen(url).read()
                except IOError:
                    return render(
                        request,
                        'commonplace/error.html',
                        { 'message' : 'The webpage at your specified URL does not exist.' }
                    )
    
                
                item = form.save(commit=False)
                
                # Populate article item with data.
                doc = ReadableDocument(html)
                summary = doc.summary()
                summary = re.sub(r'</?html>','', summary)
                summary = re.sub(r'</?body>','', summary)
                item.title = doc.short_title()
                item.fulltext = summary
            
            # Perform logic for pictures.
            elif item_type == 'picture':
                
                # Validate URL.
                try:
                    thumbnail = make_thumbnail(url, (256,256))
                except IOError: # Thrown if PIL could not load the thumbnail.
                    return render(
                        request,
                        'commonplace/error.html',
                        { 'message' : 'The image at your specified URL does not exist or is an unsupported format. Supported formats: jpeg, png, and gif.' }
                    )

                item = form.save(commit=False)

                # Deal with the thumbnail.
                temp_handle = StringIO()
                thumbnail.save(temp_handle, 'JPEG')
                temp_handle.seek(0)
                
                # Save thumbnail to a SimpleUploadedFile which can be saved into an ImageField.
                suf = SimpleUploadedFile(os.path.split(url)[-1], temp_handle.read(), content_type='JPEG')
                item.thumbnail = suf
            
            # Perform logic for videos.
            else:
                
                item = form.save(commit=False)

                # Save screenshot to a SimpleUploadedFile which can be saved into an ImageField.
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
                    item.screenshot = suf
            
            # Save item in database.
            item.user = request.user
            item.save()
            form.save_m2m()

            # Check for new categories from form.
            new_categories = form.data.get('new_categories')
            if new_categories is not None:
                process_new_categories(item, new_categories)

            # Navigate to item detail page of the newly-submitted item.
            return HttpResponseRedirect(reverse('item_detail', kwargs={ 'pk' : item.pk }))
    
    # Display page with form.
    return render(request, 'commonplace/edit_item.html', { 'item_type' : item_type, 'form' : form })

# View search results matching the specified search string.
def search_items(request):
    if request.method == 'POST':
        
        # Obtain user input for search string from POST data.
        search_string = request.POST.get('search_string')
        items = []
        
        # Check for empty or blank string.
        if search_string.strip():
        
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
