from django.contrib.auth import views as auth
from django.urls import path
from tracker import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.sign_in, name="login"),
    path("signup/", views.sign_up, name="signup"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("password/", auth.PasswordChangeView.as_view(template_name="registration/password.html", success_url="/"), name="password_change"),
    path("api/records/", views.records, name="records"),
    path("health/", views.health, name="health"),
    path("app.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
]
