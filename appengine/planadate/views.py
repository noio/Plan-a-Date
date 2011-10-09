### Imports ###

# Python imports
import logging
import urllib

# AppEngine imports
from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import urlfetch



# Django imports
from django import forms
from django.shortcuts import render_to_response
from django.conf import settings as django_settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.template import Template, Context
from django.template.loader import render_to_string
from django.template import Context, Template, RequestContext
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils import simplejson
from models import Activity
#from django.core.exceptions import ValidationError

# Library imports

# Local Imports
import models

### Constants ###
SEARCH_RADIUS_PLACES = 10000
API_KEY = "AIzaSyCDVMO3-PEsnU22lgvjp0ltnqMwW4R8TE4"
LOCATION = {"lat" : 52.37021570, "lng" : 4.895167900000001}


### Decorators for Request Handlers ###
def admin_required(func):
    """Decorator that insists that you're logged in as administrator."""
    
    def admin_wrapper(request, *args, **kwds):
        if request.user is None:
            return HttpResponseRedirect(
                users.create_login_url(request.get_full_path().encode('utf-8')))
        if not request.user_is_admin:
            return HttpResponseForbidden('You must be admin for this function')
        return func(request, *args, **kwds)
    
    return admin_wrapper

### Page Handlers ###

def frontpage(request):
    """ Renders the frontpage/redirects to mobile front page
    """
    return render_to_response('front.html')
    
def activities(request):
    act = models.Activity.all()
    return render_to_response('activities.html',{'activities':act})

def places(request):
    places = models.Place.all()
    return render_to_response('activities.html',{'places':places})

def make_plan(request):
    response_params = {}
    
    # Get the activities, and then we should make some smart choices here :)
    if request.POST['sex'] == 'male':
        activity = models.Activity.all()[0]
    else:
        activity = models.Activity.all()[1]
    
    response_params['activities'] = [activity]

    return render_to_response('plan.html',response_params)

@admin_required
def place_edit(request):
    pass

@admin_required
def place_add(request):
    response_params = {}
    response_params['places'] = models.Place.all()
    
    if 'search_term' in request.POST and request.POST['search_term'] != '':
        params = urllib.urlencode({'radius': SEARCH_RADIUS_PLACES, 'name': request.POST['search_term'], 'key': API_KEY, 'sensor': 'false'})
        url = "https://maps.googleapis.com/maps/api/place/search/json?location=%s&%s" % (str(LOCATION['lat']) + ',' + str(LOCATION['lng']), params)
        f = urlfetch.fetch(url)
        results = simplejson.loads(f.content)
        response_params['results'] = results['results']

    elif 'picked_place' in request.POST:
        ref = request.POST['picked_place']
        params = urllib.urlencode({'reference': ref, 'key': API_KEY, 'sensor': 'false'})        
        url = "https://maps.googleapis.com/maps/api/place/details/json?%s" % params
        f = urlfetch.fetch(url)
        results = simplejson.loads(f.content)
        place = models.Place(name=results["result"]["name"], location=db.GeoPt(results["result"]["geometry"]["location"]["lat"], results["result"]["geometry"]["location"]["lng"]), uris=[ref], tags=results["result"]["types"])
        place.put()
    
    return render_to_response('add-place.html', response_params)
### Helper functions ###

@admin_required
def activity_add(request):
    response_params = {}
    return render_to_response('add-activity.html', response_params)

@admin_required
def activity_edit(request):
    pass

