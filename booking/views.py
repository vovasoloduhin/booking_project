from datetime import date
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.tokens import default_token_generator

from .forms import BookingForm, RegisterForm
from .models import Booking, Room


def room_list(request):
    rooms = Room.objects.filter(is_available=True)
    room_type = request.GET.get("type", "").strip()
    if room_type:
        rooms = rooms.filter(room_type=room_type)

    types = Room.objects.filter(is_available=True).values_list("room_type", flat=True).distinct()
    return render(request, "booking/room_list.html", {"rooms": rooms, "types": types, "selected_type": room_type})


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, "booking/room_detail.html", {"room": room})


@login_required
def create_booking(request, room_id):
    room = get_object_or_404(Room, id=room_id, is_available=True)

    if request.method == "POST":
        form = BookingForm(request.POST, room=room, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.room = room
            booking.status = "pending"
            booking.save()

            messages.success(request, "Бронювання створено. Очікуйте підтвердження адміністратора.")
            return redirect("my_bookings")
    else:
        form = BookingForm(room=room, user=request.user)

    return render(request, "booking/booking_form.html", {"form": form, "room": room})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related("room")
    return render(request, "booking/my_bookings.html", {"bookings": bookings})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status != "cancelled":
        booking.status = "cancelled"
        booking.save(update_fields=["status"])
        messages.success(request, "Бронювання скасовано.")
    return redirect("my_bookings")


def register(request):
    if request.user.is_authenticated:
        return redirect("room_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            token = default_token_generator.make_token(user)
            confirmation_url = request.build_absolute_uri(
                reverse("confirm_email", args=[user.pk, token])
            )

            send_mail(
                "Підтвердження реєстрації",
                f"Вітаємо! Підтвердіть email за посиланням:\n{confirmation_url}",
                None,
                [user.email],
            )

            messages.success(
                request,
                "Реєстрацію створено. У режимі розробки посилання підтвердження буде виведено в терміналі.",
            )
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


def confirm_email(request, user_id, token):
    user = get_object_or_404(User, pk=user_id)

    if user.is_active:
        messages.info(request, "Email вже підтверджено.")
        return redirect("login")

    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)
        messages.success(request, "Email підтверджено. Ви увійшли в систему.")
        return redirect("room_list")

    messages.error(request, "Посилання недійсне або застаріло.")
    return redirect("register")


def availability(request):
    rooms = Room.objects.filter(is_available=True)
    selected_room = request.GET.get("room", "")
    return render(
        request,
        "booking/availability.html",
        {"rooms": rooms, "selected_room": selected_room},
    )


@require_GET
def availability_api(request):
    room_id = request.GET.get("room")
    start = request.GET.get("start")
    end = request.GET.get("end")

    if not room_id or not start or not end:
        return JsonResponse({"available": False, "error": "Потрібні room, start та end."}, status=400)

    try:
        room = Room.objects.get(pk=room_id, is_available=True)
        from django.utils.dateparse import parse_datetime
        start_dt = parse_datetime(start)
        end_dt = parse_datetime(end)
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)
    except (Room.DoesNotExist, TypeError, ValueError):
        return JsonResponse({"available": False, "error": "Некоректні дані."}, status=400)

    if start_dt >= end_dt:
        return JsonResponse({"available": False, "error": "Некоректний період."})

    conflict = Booking.objects.filter(
        room=room,
        start_datetime__lt=end_dt,
        end_datetime__gt=start_dt,
    ).exclude(status="cancelled").exists()

    return JsonResponse({"available": not conflict})


@require_GET
def calendar_api(request):
    room_id = request.GET.get("room")
    month = request.GET.get("month")

    bookings = Booking.objects.exclude(status="cancelled").select_related("room")

    if room_id:
        bookings = bookings.filter(room_id=room_id)

    if month:
        try:
            year, month_num = [int(x) for x in month.split("-")]
            first = date(year, month_num, 1)
            if month_num == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month_num + 1, 1)
            bookings = bookings.filter(
                start_datetime__date__lt=next_month,
                end_datetime__date__gte=first,
            )
        except ValueError:
            pass

    data = [
        {
            "room": b.room.name,
            "start": timezone.localtime(b.start_datetime).isoformat(),
            "end": timezone.localtime(b.end_datetime).isoformat(),
            "status": b.status,
        }
        for b in bookings
    ]
    return JsonResponse({"bookings": data})
