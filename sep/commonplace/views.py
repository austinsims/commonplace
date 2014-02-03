from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views import generic

from commonplace.models import Item, Category

# Front page; right now, just list latest ten items
def index(request):
    latest_items = Item.objects.order_by('-creation_date')[:10]
    context = {'latest_items' : latest_items}
    return render(request, 'commonplace/index.html', context)

# # View details of an item
# def detail(request, item_id):
#     try:
#         item = Item.objects.get(pk=item_id)
#     except Item.DoesNotExist:
#         raise Http404
#     return render(request, 'commonplace/detail.html', {
#             'item' : item,
#             'category_list' : item.categories.all(),
#             })

class DetailView(generic.DetailView):
    model = Item
#    template_name = 'commonplace/item_detail.html'

# TODO: debug failure on anonymous user login
def my_items(request):
    if request.user.is_authenticated:
        mine = Item.objects.filter(user=request.user)
        context = { 'my_items' : mine }
    else:
        context = dict()
    return render(request, 'commonplace/my_items.html', context)

# View items in a certain category
def category(request, category_name):
    try:
        cat = Category.objects.get(name=category_name)
        items = cat.item_set.all()
    except Category.DoesNotExist:
        raise Http404
    return render(request, 'commonplace/category.html', {
            'category' : cat,
            'items' : items,
            })
