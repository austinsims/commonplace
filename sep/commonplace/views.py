from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.utils import timezone

from readability.readability import Document as ReadableDocument
import urllib
import re

from commonplace.models import Article, Video, Picture, Item, Category
from commonplace.forms import ArticleForm
from django.contrib.auth import get_user_model
User = get_user_model()

class ItemListView(generic.ListView):
    model = Item

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

class ItemDetailView(generic.DetailView):
    model = Item

class ArticleDetailView(generic.DetailView):
    model = Article

def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.user.pk is item.user.pk:
        if request.method == 'POST':
            item.delete()
            return redirect('my_items')
    else:
        return render(request, 'commonplace/error.html', {'message' : 'Sorry, you aren\'t allowed to delete that!'})
    return render(request, 'commonplace/item_confirm_delete.html', {'item' : item })

def user_detail(request, pk):
    user = User.objects.get(pk=pk)
    ctx = { 'user' : user }
    return render(request, 'commonplace/user_detail.html', ctx)

# Front page; right now, just list latest ten items
def index(request):
    latest_articles = Article.objects.order_by('-creation_date')[:10]
    context = {'latest_articles' : latest_articles}
    return render(request, 'commonplace/index.html', context)

# TODO: Generalize Article, Video, Picture create views into CreateItem, then
# subclass from there

def item_detail(self, pk):
    #not yet implemented...
    pass

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
                    html = urllib.urlopen(url).read()
                except IOError:
                    # TODO: Make a template for this error message and render it
                    return HttpResponse('Sorry, the picture at your URL %s does not exist!' % url)

                # doc = ReadableDocument(html)
                # summary = doc.summary()
                # summary = re.sub(r'</?html>','', summary)
                # summary = re.sub(r'</?body>','', summary)
                # article = form.save(commit=False)

                # article.title = doc.short_title()
                # article.fulltext = summary
                # article.user = request.user
                # article.save()
                # form.save_m2m()

                return HttpResponseRedirect(reverse('item_detail', kwargs={'pk' : article.pk}))

    return render(request, 'commonplace/edit_picture.html', {
            'form' : form,
            })

# TODO: debug failure on anonymous user login
def my_items(request):
    if request.user.is_authenticated():
        mine = Item.objects.filter(user=request.user)
        context = { 'my_items' : mine }
    else:
        context = dict()
    return render(request, 'commonplace/my_items.html', context)

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
