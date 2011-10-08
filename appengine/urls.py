from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r"^$", "planadate.views.frontpage"),
	(r"^activities/$", "planadate.views.activities"),
	(r'^add_place/$', "planadate.views.add_place")
)
