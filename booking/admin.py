from django.contrib import admin
from .models import Room, Profile, Booking


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'number',
                    'capacity',
                    'price',
                    'is_available',
                    )

    list_filter = ('is_available',
                   'room_type',
                   )

    search_fields = ('name',
                     'description',
                     )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'phone',
                    )

    search_fields = ('user__username',
                     'user__email',
                     'phone',
                     )

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'room',
                    'start_datatime',
                    'end_datatime',
                    'status',
                    'created_at',
                    )

    list_filter = ('status',
                   'room',
                   )

    search_fields = ('user__username',
                     'room__name',
                     )

