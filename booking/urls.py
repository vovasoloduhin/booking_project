from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.room_list, name="room_list"),
    path("room/<int:room_id>/", views.room_detail, name="room_detail"),
    path("room/<int:room_id>/book/", views.create_booking, name="create_booking"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),

    path("register/", views.register, name="register"),
    path("confirm-email/<int:user_id>/<str:token>/", views.confirm_email, name="confirm_email"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("availability/", views.availability, name="availability"),
    path("api/availability/", views.availability_api, name="availability_api"),
    path("api/calendar/", views.calendar_api, name="calendar_api"),
]
