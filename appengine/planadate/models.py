### Imports ###

# Python Imports
import os
import re
import logging
from datetime import datetime, date, time, timedelta

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
            return timedelta(seconds=value)

class DateTemplate(db.Model):
    """ Represents a date template, that has a 
        one-to-many relationship with DateTemplateBlocks
    """
    name = db.StringProperty()
    
class DateTemplateBlock(db.Model):
    """ One block, that can be filled by an ActivityAtPlace
    """
    template       = db.ReferenceProperty(DateTemplate, collection_name="blocks",required=True)
    tags_include   = db.ListProperty(item_type=db.Key,default=[])
    tags_exclude   = db.ListProperty(item_type=db.Key,default=[])
    start_min      = db.TimeProperty(required=True)
    start_max      = db.TimeProperty(required=True)
    
    def satisfy(self, max_price, (from_min, from_max), (until_min, until_max), day):
        logging.info(max_price)
        logging.info(from_max)
        # Modify to given day
        start_min = datetime.combine(day, self.start_min)
        start_max = datetime.combine(day, self.start_max)
        # If the earliest we can start this block is later
        # than the latest we are allowed to, return no matches.
        if from_min > start_max or from_max < start_min:
            return []
        # Filter for AaPs
        aaps = ActivityAtPlace.all()
        # Filter by price
        aaps.filter('price <=', max_price)
        # Filter include tags
        logging.info(list(aaps))
        logging.info([tag.name() for tag in self.tags_include])
        for tag in self.tags_include:
            aaps.filter('tags = ', tag)
        # Filter duration
        logging.info(list(aaps))
        start_min = max(from_min, start_min)
        start_max = min(from_max, start_max)
        aaps = (a for a in aaps if a.duration_min < until_max - start_min)
        aaps = (a for a in aaps if a.duration_max > until_min - start_max)
        # Filter exclude tags
        aaps = (aap for aap in aaps if not set(aap.tags) & set(self.tags_exclude))
        return list(aaps)
        

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
    def new(cls, activity, place):
        key_name = '%d-%d'%(activity.key().id(), place.key().id())
        a = cls(key_name=key_name)
        a.activity = activity
        a.place = place
        # Compute combined properties
        a.tags = list(set(activity.tags + place.tags))
        a.price = place.price or activity.price
        a.duration_min = activity.duration_min
        a.duration_max = activity.duration_max
        return a


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

def timedelta_to_seconds(td):
    return td.days*86400 + td.seconds

def time_sub(t1, t2):
    td = date.today()
    return datetime.combine(td, t1) - datetime.combine(td, t2)