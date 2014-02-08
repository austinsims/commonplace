from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views import generic
#import forms

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
class CreateArticleView(generic.CreateView):
    model = Article
    template_name = 'commonplace/edit_article.html'
    form_class = ArticleForm

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
