from django import template

register = template.Library()


@register.filter
def human_list_with_commas(obj_list):
    if not obj_list:
        return ""

    # also force to string.
    l = len(obj_list)
    if l == 1:
        return "%s" % obj_list[0]

    # Oxford comman or not ?!
    return (
        ", ".join(str(obj) for obj in obj_list[: l - 1])
        + " and "
        + str(obj_list[l - 1])
    )
