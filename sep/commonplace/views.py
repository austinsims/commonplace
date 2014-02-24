from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

# For making thumbnails & screenshots
from PIL import Image, ImageOps
from cStringIO import StringIO
import gdata.youtube.service

# For making article summaries
from readability.readability import Document as ReadableDocument
import urllib
import re
import os

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

# Commonplace views

# Front page; right now, just list latest ten items
def index(request):
    latest_articles = Article.objects.order_by('-creation_date')[:10]
    latest_pictures = Picture.objects.order_by('-creation_date')[:10]
    latest_videos = Video.objects.order_by('-creation_date')[:10]
    context = {
        'latest_articles' : latest_articles,
        'latest_pictures' : latest_pictures,
        'latest_videos' : latest_videos,
        }
    return render(request, 'commonplace/index.html', context)

# TODO: debug failure on anonymous user login
def my_items(request):
    if request.user.is_authenticated():
        my_articles = Article.objects.filter(user=request.user)
        my_pictures = Picture.objects.filter(user=request.user)
        my_videos = Video.objects.filter(user=request.user)
        context = { 
            'my_articles' : my_articles,
            'my_pictures' : my_pictures,
            'my_videos' : my_videos,
            }
        return render(request, 'commonplace/my_items.html', context)
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t logged in!'})

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
# TODO: Generalize Article, Video, Picture create views into CreateItem, then
# subclass from there

class ItemListView(generic.ListView):
    model = Item

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

class ItemDetailView(generic.DetailView):
    model = Item

def item_detail(self, pk):
    #not yet implemented...
    pass

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

class ArticleDetailView(generic.DetailView):
    model = Article

def update_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.user.pk is article.user.pk:
        form = ArticleForm(request.POST or None, instance=article)
        if form.is_valid():
            form.save()
            return redirect('my_items')
        template_name = 'commonplace/edit_article.html'
        return render(request, template_name, {'form' : form})
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to edit that!'})

def submit_article(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})
    else:
        if request.method == 'GET':
            form = ArticleForm()
        else:
            # POST request: handle form upload.
            form = ArticleForm(request.POST) # bind data from request

            # If data is valid, create article and redirect
            if form.is_valid():

                # Retrieve short title and readable text
                url = form.cleaned_data['url']
                try:
                    html = urllib.urlopen(url).read()
                except IOError:
                    # TODO: Make a template for this error message and render it
                    return HttpResponse('Sorry, the webpage at your URL %s does not exist!' % url)
                    return render(request, 'commonplace/error.html', {'message' : 'Sorry, the webpage at your URL %s does not exist!' % url})

                doc = ReadableDocument(html)
                summary = doc.summary()
                summary = re.sub(r'</?html>','', summary)
                summary = re.sub(r'</?body>','', summary)
                article = form.save(commit=False)

                article.title = doc.short_title()
                article.fulltext = summary
                article.user = request.user
                article.save()
                form.save_m2m()

                return HttpResponseRedirect(reverse('article_detail', kwargs={'pk' : article.pk}))

        return render(request, 'commonplace/edit_article.html', {
                'form' : form,
                })

# Picture views

class PictureDetailView(generic.DetailView):
    model = Picture

def submit_picture(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})
    else:
        if request.method == 'GET':
            form = PictureForm()
        else:
            # POST request: handle form upload.
            form = PictureForm(request.POST) # bind data from request

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

                return HttpResponseRedirect(reverse('picture_detail', kwargs={'pk' : picture.pk}))

    return render(request, 'commonplace/edit_picture.html', {
            'form' : form,
            })

def update_picture(request, pk):
    picture = get_object_or_404(Picture, pk=pk)
    if request.user.pk is picture.user.pk:
        form = PictureForm(request.POST or None, instance=picture)
        if form.is_valid():
            form.save()
            return redirect('my_items')
        template_name = 'commonplace/edit_picture.html'
        return render(request, template_name, {'form' : form})
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to edit that!'})

# Picture views

class PictureDetailView(generic.DetailView):
    model = Picture

def submit_picture(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})
    else:
        if request.method == 'GET':
            form = PictureForm()
        else:
            # POST request: handle form upload.
            form = PictureForm(request.POST) # bind data from request

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

                return HttpResponseRedirect(reverse('picture_detail', kwargs={'pk' : picture.pk}))

    return render(request, 'commonplace/edit_picture.html', {
            'form' : form,
            })

def update_picture(request, pk):
    picture = get_object_or_404(Picture, pk=pk)
    if request.user.pk is picture.user.pk:
        form = PictureForm(request.POST or None, instance=picture)
        if form.is_valid():
            form.save()
            return redirect('my_items')
        template_name = 'commonplace/edit_picture.html'
        return render(request, template_name, {'form' : form})
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to edit that!'})

# Video views

class VideoDetailView(generic.DetailView):
    model = Video

def submit_video(request):
    if not request.user.is_authenticated():
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to submit new things! Please login!'})
    else:
        if request.method == 'GET':
            form = VideoForm()
        else:
            # POST request: handle form upload.
            form = VideoForm(request.POST) # bind data from request

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

                return HttpResponseRedirect(reverse('video_detail', kwargs={'pk' : video.pk}))

    return render(request, 'commonplace/edit_video.html', {
            'form' : form,
            })

def update_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if request.user.pk is video.user.pk:
        form = VideoForm(request.POST or None, instance=video)
        if form.is_valid():
            form.save()
            return redirect('my_items')
        template_name = 'commonplace/edit_video.html'
        return render(request, template_name, {'form' : form})
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to edit that!'})


# User views

def user_detail(request, pk):
    user = User.objects.get(pk=pk)
    ctx = { 'user' : user }
    return render(request, 'commonplace/user_detail.html', ctx)
