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

    url(r'^tinymce/', include('tinymce.urls')),

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
    url(r'^user_preferences', views.user_preferences, name='user_preferences'),
    # TODO: use username instead of pk for user detail URL
    url(r'^user/(?P<pk>\d+)$', views.user_detail, name='user_detail'),
    
    # Item URLs,
    url(r'^create/item', views.submit_item, name='create_item'),
    
    # Folder URLs
    url(r'^create/folder', views.FolderCreate.as_view(), name='create_folder'),

    url(r'^likes/$', views.likes, name='likes'),
    url(r'^like/(?P<pk>\d+)$', views.like, name='like'),
    url(r'^unlike/(?P<pk>\d+)$', views.unlike, name='unlike'),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
