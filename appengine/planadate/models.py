### Imports ###

# Python Imports
import os
import re
import datetime

# AppEngine Imports
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.ext.db import Key
from google.appengine.ext.db import BadValueError, KindError

# Django Imports
import django.template as django_template
from django.template import Context, TemplateDoesNotExist
from google.appengine.ext.db import djangoforms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string, get_template
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.db import models

### Constants ###

### Exceptions ###

### Models ###

class TimeDeltaProperty(db.Property):
    """ In seconds """
    def get_value_for_datastore(self, model_instance):
        td = super(TimeDeltaProperty, self).get_value_for_datastore(model_instance)
        if td is not None:
            return (td.seconds + td.days * 86400)
        return None
    
    def make_value_from_datastore(self, value):
        if value is not None:
            return datetime.timedelta(seconds=value)


class Activity(db.Model):
    created      = db.DateTimeProperty(auto_now_add=True)
    tags         = db.ListProperty(item_type=db.Key)
    name         = db.StringProperty(required=True)
    price        = db.IntegerProperty()
    duration_min = TimeDeltaProperty()
    duration_max = TimeDeltaProperty()

class ActivityForm(djangoforms.ModelForm):
    class Meta:
        model = Activity
    
class Place(db.Model):
    location   = db.GeoPtProperty()
    address    = db.PostalAddressProperty()
    tags       = db.ListProperty(item_type=db.Key)
    name       = db.StringProperty(required=True)
    uris       = db.StringListProperty()
    activities = db.ListProperty(item_type=db.Key)
    
class BusinessHours(db.Model):
    day   = db.IntegerProperty(choices=set([0,1,2,3,4,5,6]))
    opened  = db.TimeProperty()
    closed = db.TimeProperty()
    date  = db.DateProperty()
    place = db.ReferenceProperty(Place, collection_name='business_hours')

class Tag(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)

    def __init__(self, key_name, **kwargs):
       db.Model.__init__(self, key_name=key_name, **kwargs)
    
### Helper Functions ###
