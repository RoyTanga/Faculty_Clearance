from django import template

register = template.Library()

@register.filter
def get_document(clearance_set, clearance_type):
    return clearance_set.documents.filter(clearance_type=clearance_type).first()

