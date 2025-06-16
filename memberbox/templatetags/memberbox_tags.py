from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def render_box_item(item):
    """
    Render a box item using a separate template.
    Usage: {% render_box_item item %}
    """
    return render_to_string("memberbox/_box_item.html", {"item": item})


@register.inclusion_tag("memberbox/_box_item.html")
def box_item(item):
    """
    Include tag for rendering a box item.
    Usage: {% box_item item %}
    """
    return {"item": item}
