from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views import generic

from readability.readability import Document as ReadableDocument
import urllib
import re

from commonplace.models import Article, Video, Picture, Item, Category
from commonplace.forms import ArticleForm
from django.contrib.auth import get_user_model
User = get_user_model()

# Front page; right now, just list latest ten items
def index(request):
    latest_items = Item.objects.order_by('-creation_date')[:10]
    context = {'latest_items' : latest_items}
    return render(request, 'commonplace/index.html', context)

class ItemDetailView(generic.DetailView):
    model = Item

class UserDetailView(generic.DetailView):
    model = User
    template_name = 'commonplace/user_detail.html'

# TODO: Generalize Article, Video, Picture create views into CreateItem, then
# subclass from there
# class CreateArticleView(generic.FormView):
#     model = Article
#     template_name = 'commonplace/edit_article.html'
#     form_class = ArticleForm

def submit_article(request):
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

            return HttpResponseRedirect(reverse('item_detail', kwargs={'pk' : article.pk}))

    return render(request, 'commonplace/edit_article.html', {
            'form' : form,
            })

# TODO: debug failure on anonymous user login
def my_items(request):
    if request.user.is_authenticated:
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
def items_by_user(request, user_name):
    try:
        user = User.objects.get(username=user_name)
        items = user.item_set.all()
    except User.DoesNotExist:
        raise Http404
    return render(request, 'commonplace/items_by_user.html', {
            'user' : user,
            'items' : items,
            })
