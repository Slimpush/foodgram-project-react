from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin
from users.models import User


@register(User)
class Admin(UserAdmin):
    fields = (
        ('is_active', ),
        ('username', 'email', ),
        ('first_name', 'last_name', ),
    )
    fieldsets = []
    list_display = (
        'is_active', 'username', 'first_name', 'last_name', 'email',
    )
    list_filters = ('is_active', 'email', 'first_name', )
    search_fields = ('username', 'email', )
