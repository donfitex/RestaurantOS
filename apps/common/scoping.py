from django.db.models import Q
from apps.users.permissions import is_admin


def staff_branches(user):
    from apps.restaurants.models import Branch
    if is_admin(user):
        return Branch.objects.filter(is_active=True, restaurant__is_active=True)
    return Branch.objects.filter(Q(staff=user) | Q(managers=user), is_active=True, restaurant__is_active=True).distinct()


def scope_branches(queryset, user, field="branch"):
    if is_admin(user):
        return queryset
    return queryset.filter(**{f"{field}__in": staff_branches(user)})
