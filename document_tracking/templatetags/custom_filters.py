"""
Custom template filters for Document Tracking.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
