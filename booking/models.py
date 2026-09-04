from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Room(models.Model):
    name = models.CharField("Назва", max_length=100)
    room_type = models.CharField("Тип", max_length=100)
    description = models.TextField("Опис", blank=True)
    capacity = models.PositiveIntegerField("Місткість")
    price = models.DecimalField("Ціна за годину", max_digits=10, decimal_places=2)
    features = models.TextField("Особливості", blank=True)
    is_available = models.BooleanField("Доступна", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "кімната"
        verbose_name_plural = "кімнати"

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("Телефон", max_length=30, blank=True)

    class Meta:
        verbose_name = "профіль"
        verbose_name_plural = "профілі"

    def __str__(self):
        return self.user.username


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Очікує підтвердження"),
        ("confirmed", "Підтверджено"),
        ("cancelled", "Скасовано"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    start_datetime = models.DateTimeField("Початок")
    end_datetime = models.DateTimeField("Завершення")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        ordering = ["-start_datetime"]
        verbose_name = "бронювання"
        verbose_name_plural = "бронювання"

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError("Початок бронювання повинен бути раніше завершення.")

            if self.start_datetime < timezone.now():
                raise ValidationError("Не можна створити бронювання в минулому.")

        if self.room_id and not self.room.is_available:
            raise ValidationError("Ця кімната зараз недоступна.")

        if self.room_id and self.start_datetime and self.end_datetime:
            conflicts = Booking.objects.filter(
                room=self.room,
                start_datetime__lt=self.end_datetime,
                end_datetime__gt=self.start_datetime,
            ).exclude(pk=self.pk).exclude(status="cancelled")

            if conflicts.exists():
                raise ValidationError("Ця кімната вже заброньована на вибраний період.")

    @property
    def total_price(self):
        if not self.start_datetime or not self.end_datetime:
            return 0
        seconds = (self.end_datetime - self.start_datetime).total_seconds()
        hours = seconds / 3600
        return round(float(self.room.price) * hours, 2)

    def __str__(self):
        return f"{self.user.username} — {self.room.name}"
