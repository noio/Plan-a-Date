### Imports ###

# Python imports
import logging
import urllib
import datetime

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
from models import Activity, ActivityForm
#from django.core.exceptions import ValidationError

# Library imports
import datetime

# Local Imports
import models

### Constants ###
SEARCH_RADIUS_PLACES = 10000
API_KEY = "AIzaSyCDVMO3-PEsnU22lgvjp0ltnqMwW4R8TE4"
LOCATION = {"lat" : 52.37021570, "lng" : 4.895167900000001} # TODO: Lelijk


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

def plan(request):
    response_params = {}
    response_params['base_template'] = 'ajax.html' if request.is_ajax() else 'base.html' 
    
    # Extract form
    start_time = datetime.datetime.strptime(request.POST['start_time'], '%H:%M').time()
    end_time = datetime.datetime.strptime(request.POST['end_time'], '%H:%M').time()
    max_price = int(request.POST['max_price'])
    # TODO: Some smart stuff to select a template
    selected_template = models.DateTemplate.all().get()
    # (deleteme) create a new template if there is none
    if selected_template is None:
        selected_template = models.DateTemplate(name = "Example Template")
        selected_template.put()
        models.DateTemplateBlock(template=d, moment = datetime.time(hour=15), tags_exclude=["eten"]).put()
        models.DateTemplateBlock(template=d, moment = datetime.time(hour=19), tags_include=["eten"]).put()
    
    def plan_rest(from_time, blocks, money_left):
        """ Recursive function to make a plan
        """
        # We're done, return an empty list
        if not blocks:
            return []
        if len(blocks) > 1:
            until_time = (blocks[1].start_min, blocks[1].start_max)
        else:
            until_time = (end_time,end_time)
        plans = []
        for option in blocks[0].satisfy(money_left, from_time, until_time):
            start_min = max(from_time[0], option.start_min)
            start_max = min(from_time[1], option.start_max)
            new_from_time = (start_min + option.duration_min, start_max + option.duration_max)
            blocks = blocks[1:]
            rest_plans = plan_rest(new_from_time, blocks, money_left - option.price)
            plans.extend([option] + rp for rp in rest_plans if len(rp) == len(blocks))
        return plans
    
    plans = plan_rest((start_time, start_time), selected_template.blocks.fetch(100), max_price)
    response_params['plans'] = plans
    return render_to_response('plan.html',response_params)
    
def activities(request):
    act = models.Activity.all()
    return render_to_response('activities.html',{'activities':act})

def places(request):
    places = models.Place.all()
    #tags = [tag.key().name() for tag in places]
    return render_to_response('places.html',{'places':places})

@admin_required
def place_edit(request):
    pass

@admin_required
def place_add(request):
    current_activities = [activity.name for activity in models.Activity.all()]
    current_tags = [tag.key().name() for tag in models.Tag.all()]
    
    response_params = {}
    response_params['places'] = models.Place.all()
    response_params['current_tags'] = current_tags
    response_params['current_activities'] = current_activities
    response_params['added'] = ""

    
    #Searching
    if 'search' in request.POST:
        
        params = urllib.urlencode({'radius': SEARCH_RADIUS_PLACES, 'name': request.POST['search_term'], 'key': API_KEY, 'sensor': 'false'})
        url = "https://maps.googleapis.com/maps/api/place/search/json?location=%s&%s" % (str(LOCATION['lat']) + ',' + str(LOCATION['lng']), params)
        f = urlfetch.fetch(url)
        results = simplejson.loads(f.content)
        response_params['results'] = results['results']
    
    # adding place
    elif 'add' in request.POST and 'picked_place' in request.POST:
        ref = request.POST['picked_place']
        params = urllib.urlencode({'reference': ref, 'key': API_KEY, 'sensor': 'false'})        
        url = "https://maps.googleapis.com/maps/api/place/details/json?%s" % params
        results = simplejson.loads(urlfetch.fetch(url).content)["result"]
        
        place = models.Place(name=results["name"], 
                             address=results["formatted_address"],
                             location=db.GeoPt(results["geometry"]["location"]["lat"], 
                             results["geometry"]["location"]["lng"]), 
                             uris=[url])                             
                             
        # Take care of tags..
        applied_tags = []
         
        # Which old tags are applied?
        for tag in current_tags:
            if "tag-%s" % tag in request.POST:
                applied_tags.append(tag)
             
        # Check for new tags, put them in tag-model and add them to applied_tags
        for i in range(1,4):
            if 'newtag%d' % i in request.POST and request.POST['newtag%d-value' % i] != '':
                models.Tag.get_or_insert(key_name=request.POST['newtag%d-value' % i])
                applied_tags.append(request.POST['newtag%d-value' % i])
                            
        applied_tags = [db.Key.from_path('Tag',tagname) for tagname in applied_tags]
        place.tags = applied_tags


        # Take care of activities:
        applied_activities = []

        for activity in current_activities:
            if "activity-%s" % activity in request.POST:
                applied_activities.append(tag)    
        
        applied_activities = [db.Key.from_path('Activity',activity) for activity in applied_activities]
        place.activities = applied_activities
        
        # TODO: put activity in place-activity model
        
        place.put()
        response_params['added'] = "Succesfully added place: %s" % place.name
    
    return render_to_response('place-add.html', response_params)
### Helper functions ###

@admin_required
def activities(request):
    # Function to get all activities and handle POST request to add or edit
    # an activity
    response_params = {}
    response_params['activities'] = models.Activity.all()
    response_params['activity_form'] = ActivityForm()

    # If the form is submitted    
    if request.method == "POST":        
        tags = request.POST['tags'].split(',')

        tag_ids = []
        for tag in tags:
            if tag.strip() != '':
                # Check if the tag already exists
                t = models.Tag.get_by_key_name(tag)
                # If not add it
                if not t:
                    t = models.Tag(key_name=tag)
                    t.put()
                tag_ids.append(t.key())

        name = request.POST['name']
        price = int(request.POST['price'])

        duration_min = datetime.timedelta(seconds=floatToSeconds(float(request.POST['duration_min'])))
        duration_max = datetime.timedelta(seconds=floatToSeconds(float(request.POST['duration_max'])))

        # If we got an activity id from the request, we do an update instead of an add
        if 'activity-id' in request.POST:
            logging.info('edit an existing activity')
            activity = Activity.get_by_id(int(request.POST['activity-id']))
        else:
            activity = Activity(name=name,price=price,duration_min=duration_min,duration_max=duration_max,tags=tag_ids)
            activity.put()

    return render_to_response('activities.html', response_params)

@admin_required
def activity_edit(request, activity_id):
    response_params = {}
    response_params['activity'] = Activity.get_by_id(int(activity_id))
    return render_to_response('activity-edit.html', response_params)


# Helper functions
def get_activities_json(request):
    activities = models.Activity.all()
    activity_list = []

    for activity in activities:
        activity_list.append(activity.name)    

    return activity_list


def floatToSeconds(floatTime):
    seconds = int(floatTime * 3600)
    return seconds
