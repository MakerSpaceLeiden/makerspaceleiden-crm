from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.simple_tag
def agenda_badge(event):
    cls = "text-bg-secondary"
    if event.display_status == "completed":
        cls = "text-bg-success"

    if event.display_status == "help wanted" or event.display_status == "help_wanted":
        cls = "text-bg-warning"

    if event.display_status == "pending":
        return ""

    if event.display_status == "in_progress":
        cls = "text-bg-info"

    if event.display_status == "overdue":
        cls = "text-bg-danger"

    return mark_safe(
        f'<div data-test-hook="status:{event.display_status}" class="badge {cls}">{event.display_status.replace("_", " ").title()}</div>'
    )
