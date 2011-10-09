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

class DateTemplate(db.Model):
    """ Represents a date template, that has a 
        one-to-many relationship with DateTemplateBlocks
    """
    name = db.StringProperty()
    
class DateTemplateBlock(db.Model):
    """ One block, that can be filled by an ActivityAtPlace
    """
    template       = db.ReferenceProperty(DateTemplate, collection_name="blocks")
    tags_include   = db.ListProperty(item_type=db.Key)
    tags_exclude   = db.ListProperty(item_type=db.Key)
    start_min      = db.TimeProperty()
    start_max      = db.TimeProperty()
    
    def satisfy(self, max_price, (from_min, from_max), (until_min, until_max)):
        # If the earliest we can start this block is later
        # than the latest we are allowed to, return no matches.
        if start_min > self.start_max or start_max < self.start_min:
            return []
        # Filter for AaPs
        aaps = ActivityAtPlace.all()
        aaps.filter('price <= ', max_price)
        # Filter include tags
        for tag in self.tags_include:
            aaps.filter('tags = ', tag)
        # Filter duration
        aaps.filter('duration < ', until_max - start_min)
        aaps.filter('duration > ', until_min - start_max)
        # Fetch
        aaps = aaps.fetch()
        # Filter exclude tags
        aaps = [aap for aap in aaps if not set(aap.tags) & set(self.tags_exclude)]
        return aaps
        

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

    name            = db.StringProperty(required=True)
    tags            = db.ListProperty(item_type=db.Key)
    uris            = db.StringListProperty()
    activities      = db.ListProperty(item_type=db.Key)
    price           = db.IntegerProperty()
    price_for_group = db.IntegerProperty(default=1)
    location        = db.GeoPtProperty()
    address         = db.PostalAddressProperty()

class ActivityAtPlace(db.Model):
    """ Connects an activity and a place, 
        and "caches" the values that depend
        on both.
    """
    activity     = db.ReferenceProperty(Activity)
    place        = db.ReferenceProperty(Place)
    
    tags         = db.ListProperty(db.Key)
    price        = db.IntegerProperty()
    duration_min = TimeDeltaProperty()
    duration_max = TimeDeltaProperty()
    
    @classmethod
    def new(activity, place):
        key_name = '%d-%d'%(activity.key().id(), place.key().id())
        a = ActivityAtPlace(key_name=key_name)
        a.activity = activity
        a.place = place
        # Compute combined properties
        a.tags = set(activity.tags + place.tags)
        a.price = place.price or activity.price
        a.duration_min = activity.duration_min
        a.duration_max = activity.duration_max


class BusinessHours(db.Model):
    day    = db.IntegerProperty(choices=set([0,1,2,3,4,5,6]))
    opened = db.TimeProperty()
    closed = db.TimeProperty()
    date  = db.DateProperty()
    place = db.ReferenceProperty(Place, collection_name='business_hours')

class Tag(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)

    def __init__(self, key_name, **kwargs):
       db.Model.__init__(self, key_name=key_name, **kwargs)
### Helper Functions ###
