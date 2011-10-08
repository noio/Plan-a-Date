### Imports ###

# Python imports
import logging

# AppEngine imports
from google.appengine.ext import db
from google.appengine.api import users

# Django imports
from django import forms
from django.shortcuts import render_to_response
from django.conf import settings as django_settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.template import Context, Template, RequestContext
from django.core.urlresolvers import reverse
from django.utils import simplejson
from models import Activity
#from django.core.exceptions import ValidationError

# Library imports

# Local Imports
import models

### Constants ###

### Decorators for Request Handlers ###


### Page Handlers ###

def frontpage(request):
    """ Renders the frontpage/redirects to mobile front page
    """
    return render_to_response('front.html')
    
def activities(request):
    act = models.Activity.all()
    return render_to_response('activities.html',{'activities':act})

def make_plan(request):
    response = RequestContext(request, {})
    
    # Get the activities, and then we should make some smart choices here :)
    if request.POST['sex'] == 'male':
        activity = models.Activity.all()[0]
    else:
        activity = models.Activity.all()[1]
    
    response['activities'] = [activity]

    return render_to_response('plan.html',response)

def add_sample_data(request):
    # Function to add some non-sense data to the DB
    a = Activity(name='Shoppen')
    a.put()
    return render_to_response('front.html',{})

### Helper functions ###

