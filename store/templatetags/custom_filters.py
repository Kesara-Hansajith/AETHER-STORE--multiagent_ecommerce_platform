from django import template

register = template.Library()

@register.filter(name='range')
def range_filter(number):
    return range(number)
