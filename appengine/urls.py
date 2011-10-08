from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r"^$", "planadate.views.frontpage"),
	(r"^activities/$", "planadate.views.activities"),
        (r"^plan/$", "planadate.views.make_plan"),

        # Url to put some-test data in the DB
        (r"^add-data/$", "planadate.views.add_sample_data"),
)
