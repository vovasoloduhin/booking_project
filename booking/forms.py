from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Booking, Room


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("start_datetime", "end_datetime")
        widgets = {
            "start_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, room=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = room
        self.user = user

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_datetime")
        end = cleaned.get("end_datetime")

        if not start or not end:
            return cleaned

        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        if timezone.is_naive(end):
            end = timezone.make_aware(end)

        if start >= end:
            raise ValidationError("Початок повинен бути раніше завершення.")

        if start < timezone.now():
            raise ValidationError("Бронювання має починатися в майбутньому.")

        if not self.room or not self.room.is_available:
            raise ValidationError("Ця кімната зараз недоступна.")

        conflicts = Booking.objects.filter(
            room=self.room,
            start_datetime__lt=end,
            end_datetime__gt=start,
        ).exclude(status="cancelled")

        if self.instance.pk:
            conflicts = conflicts.exclude(pk=self.instance.pk)

        if conflicts.exists():
            raise ValidationError("На цей період кімната вже зайнята.")

        return cleaned
