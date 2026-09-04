from django.contrib import admin
from .models import Booking, Profile, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "room_type", "capacity", "price", "is_available")
    list_filter = ("room_type", "is_available")
    search_fields = ("name", "description", "features")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "start_datetime", "end_datetime", "status", "created_at")
    list_filter = ("status", "room")
    search_fields = ("user__username", "user__email", "room__name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    list_editable = ("status",)
