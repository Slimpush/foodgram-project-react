from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin
from users.models import User


@register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'is_active',
        'username',
        'first_name',
        'last_name',
        'email',
    )
    list_filter = (
        'is_active',
        'email',
        'first_name',
    )
    search_fields = (
        'username',
        'email',
    )
