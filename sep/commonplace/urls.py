from django.conf.urls import patterns, url
from commonplace import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index')
)
