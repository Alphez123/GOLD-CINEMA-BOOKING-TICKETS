from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Movie, Booking

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'balance', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('balance', 'customer_id', 'phone', 'address', 'city', 'zip_code')}),
    )

class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'duration']

class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie_name', 'date', 'time', 'created_at']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(Booking, BookingAdmin)
