from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r"^$", "planadate.views.frontpage"),
    (r"^plan/$", "planadate.views.make_plan"),
    
    (r"^activities/$", "planadate.views.activities"),
    (r"^activities/add/$", "planadate.views.activity_add"),
    (r"^activities/(\d+)/$", "planadate.views.activity_edit"),
    
    (r'^places/$', "planadate.views.places"),
    (r'^places/add/$', "planadate.views.place_add"),
    (r'^places/(\d+)/$', "planadate.views.place_edit"),
    
)
