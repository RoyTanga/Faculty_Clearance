from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClearanceSet, Document

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('is_faculty', 'is_admin')}),
    )
    list_display = UserAdmin.list_display + ('is_faculty', 'is_admin')

admin.site.register(User, CustomUserAdmin)

# Register ClearanceSet
admin.site.register(ClearanceSet)

# Register Document
admin.site.register(Document)
