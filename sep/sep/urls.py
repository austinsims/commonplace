from django.conf.urls import patterns, include, url
from commonplace import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sep.views.home', name='home'),
    # url(r'^sep/', include('sep.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Django_Facebook example URLs
    url(r'^facebook/', include('django_facebook.urls')),
    url(r'^accounts/', include('django_facebook.auth_urls')), #Don't add this line if you use django registration or userena for registration and auth.

    # Commonplace URLs
    url(r'^$', views.index, name='index'),
    url(r'^item/(?P<pk>\d+)?/$', views.ItemDetailView.as_view(), name='item_detail'),
    url(r'^create/article', views.submit_article, name='create_article'),
    url(r'^category/(?P<category_name>\w+)?/$', views.items_by_category, name='items_by_category'),
    url(r'^user/(?P<user_name>\w+)/submissions?/$', views.items_by_user, name='items_by_user'),
    # TODO: use username instead of pk for user detail URL
    url(r'^user/(?P<pk>\d+)?/$', views.UserDetailView.as_view(), name='user_detail'),
    url(r'^my_items?/$', views.my_items, name='my_items'),
)
