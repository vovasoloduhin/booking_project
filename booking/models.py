from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Room(models.Model):
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone =  models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
        ('cancelled', 'Скасовано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')

    start_datatime = models.DateTimeField()
    end_datatime = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_datatime >= self.end_datatime:
            raise ValidationError('Дата початку повинна бути раніше дати завершення')

        overlapping_bookings = Booking.objects.filter(room=self.room, start_datatime__lt=self.end_datatime, end_datatime__gt=self.start_datatime).exclude(pk=self.pk).exclude(status='cancelled')

        if overlapping_bookings.exists():
            raise ValidationError('Ця комната вже заброньована на вибраний період')

    def __str__(self):
        return f'{self.user.username} - {self.room.name}'