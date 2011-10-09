from django import template

register = template.Library()

@register.filter
def secondsToHours(seconds):
    return seconds/3600.0