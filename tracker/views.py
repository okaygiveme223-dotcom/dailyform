import hashlib
import json
import unicodedata
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import IntegrityError, connection, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import AccountRecords, AuthAttempt
from .validation import validate_records


def auth_allowed(request, action):
    # Count attempts in the database so limits survive process restarts.
    identifiers = [(action + ":global", 300)]
    if action == "login":
        username = unicodedata.normalize("NFKC", request.POST.get("username", "")).strip().casefold()[:150]
        identifiers.append(("login:" + username, 10))
    else:
        identifiers.append(("signup:" + request.META.get("REMOTE_ADDR", ""), 20))
    now = timezone.now()
    allowed = True
    with transaction.atomic():
        for identifier, limit in identifiers:
            key = hashlib.sha256(identifier.encode()).hexdigest()
            AuthAttempt.objects.get_or_create(key=key, defaults={"window": now})
            counter = AuthAttempt.objects.select_for_update().get(key=key)
            if counter.window < now - timedelta(minutes=15):
                counter.window = now
                counter.attempts = 0
            if counter.attempts >= limit:
                allowed = False
            counter.attempts = min(counter.attempts + 1, limit)
            counter.save()
            if not allowed:
                break
    return allowed


@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST" and not auth_allowed(request, "login"):
        return render(request, "registration/login.html", {"form": AuthenticationForm(request), "limited": True}, status=429)
    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "registration/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def sign_up(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST" and not auth_allowed(request, "signup"):
        return render(request, "registration/signup.html", {"form": UserCreationForm(), "limited": True}, status=429)
    form = UserCreationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
                AccountRecords.objects.create(user=user)
        except IntegrityError:
            form.add_error("username", "Choose a different username.")
        else:
            login(request, user)
            return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@require_http_methods(["GET", "PUT"])
def records(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Your session expired. Sign in again to continue."}, status=401)
    if request.method == "GET":
        account, _ = AccountRecords.objects.get_or_create(user=request.user)
        return JsonResponse({"records": account.records, "revision": account.revision})
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict) or type(data.get("revision")) is not int:
            raise ValueError("Missing revision.")
        cleaned = validate_records(data.get("records"))
    except (ValueError, TypeError, UnicodeDecodeError) as error:
        return JsonResponse({"error": str(error) or "Invalid records."}, status=400)
    with transaction.atomic():
        AccountRecords.objects.get_or_create(user=request.user)
        account = AccountRecords.objects.select_for_update().get(user=request.user)
        if account.revision != data["revision"]:
            return JsonResponse({"error": "Records changed on another device. Refresh your records, then retry this edit."}, status=409)
        account.records = cleaned
        account.revision += 1
        account.save(update_fields=["records", "revision"])
    return JsonResponse({"revision": account.revision})


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def manifest(request):
    return JsonResponse({"name": "Dailyform · Study & training", "short_name": "Dailyform", "start_url": "/", "display": "standalone", "theme_color": "#252a34", "background_color": "#f7f8fa", "icons": [{"src": f"/static/icon{size}.png", "sizes": f"{size}x{size}", "type": "image/png"} for size in (192, 512)]}, content_type="application/manifest+json")


def service_worker(request):
    return HttpResponse((Path(settings.BASE_DIR) / "static" / "sw.js").read_text(), content_type="text/javascript")
