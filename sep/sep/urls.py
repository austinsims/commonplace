from django.conf.urls import patterns, include, url
from commonplace import views
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

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
    url(r'^list/?', views.ItemListView.as_view(), name='item_list'),
    url(r'^category/(?P<category_name>\w+)$', views.items_by_category, name='items_by_category'),
    url(r'^user/(?P<pk>\w+)/submissions$', views.items_by_user, name='items_by_user'),
    url(r'^item/(?P<pk>\d+)$', views.item_detail, name='item_detail'),
    url(r'^my_items$', views.my_items, name='my_items'),
    url(r'delete/(?P<pk>\d+)$', views.item_delete, name='item_delete'),
    url(r'update/(?P<pk>\d+)$', views.item_update, name='item_update'),
    url(r'^search/items', views.search_items, name='search_items'),
    # TODO: use username instead of pk for user detail URL
    url(r'^user/(?P<pk>\d+)$', views.user_detail, name='user_detail'),

    # Article URLs
    url(r'^create/article', views.submit_article, name='create_article'),

    # Picture URLs
    url(r'^create/picture', views.submit_picture, name='create_picture'),

    # Video URLs
    url(r'^create/video', views.submit_video, name='create_video'),

    url(r'^MEDIA_ROOT/picture_thumbnails', views.test_picture, name='test_picture'),
    


)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
