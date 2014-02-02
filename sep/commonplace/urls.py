from django.conf.urls import patterns, url
from commonplace import views

urlpatterns = patterns('',
    # index
    url(r'^$', views.index, name='index'),
    # indidivual item by id, e.g. /item/5
    url(r'^(?P<item_id>\d+)/$', views.detail, name='detail'),
)
