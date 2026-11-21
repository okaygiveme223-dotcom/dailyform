import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from .models import AccountRecords


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class AccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("student", password="River-Practice-482!")
        cls.other = get_user_model().objects.create_user("another", password="River-Practice-483!")

    def setUp(self):
        self.record = {
            "id": "revision-1", "title": "Gas exchange", "date": "2026-11-21",
            "type": "Academic", "subject": "Biology 9700", "method": "Active recall", "minutes": 30,
        }

    def write_records(self, records, revision=0):
        return self.client.put("/api/records/", json.dumps({"records": records, "revision": revision}), content_type="application/json")

    def test_anonymous_cannot_access_records_or_dashboard(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertEqual(self.client.get("/api/records/").status_code, 401)
        self.assertEqual(self.write_records([self.record]).status_code, 401)

    def test_each_account_has_its_own_records(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.write_records([self.record]).status_code, 200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/records/").json()["records"], [])
        self.assertEqual(self.write_records([]).status_code, 200)
        self.assertEqual(AccountRecords.objects.get(user=self.owner).records, [self.record])

    def test_stale_device_cannot_overwrite_newer_records(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.write_records([self.record]).status_code, 200)
        self.assertEqual(self.write_records([], revision=0).status_code, 409)
        self.assertEqual(AccountRecords.objects.get(user=self.owner).records, [self.record])

    def test_invalid_import_is_atomic(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.write_records([self.record]).status_code, 200)
        self.assertEqual(self.write_records([self.record, {"title": "Bad entry"}], revision=1).status_code, 400)
        self.assertEqual(AccountRecords.objects.get(user=self.owner).records, [self.record])

    def test_writes_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.put("/api/records/", json.dumps({"records": [], "revision": 0}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        client.get("/")
        response = client.put("/api/records/", json.dumps({"records": [], "revision": 0}), content_type="application/json", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 200)

    def test_signup_login_and_post_logout(self):
        response = self.client.post("/signup/", {"username": "newstudent", "password1": "Hydrogen-River-482!", "password2": "Hydrogen-River-482!"})
        self.assertRedirects(response, "/")
        user = get_user_model().objects.get(username="newstudent")
        self.assertTrue(user.check_password("Hydrogen-River-482!"))
        self.assertNotEqual(user.password, "Hydrogen-River-482!")
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.client.post("/logout/")
        self.assertEqual(self.client.get("/api/records/").status_code, 401)
        self.assertRedirects(self.client.post("/login/", {"username": "newstudent", "password": "Hydrogen-River-482!"}), "/")

    def test_failed_logins_are_throttled(self):
        for _ in range(10):
            self.assertEqual(self.client.post("/login/", {"username": "student", "password": "wrong"}).status_code, 200)
        self.assertEqual(self.client.post("/login/", {"username": "student", "password": "wrong"}).status_code, 429)

    def test_private_responses_are_not_cached(self):
        self.client.force_login(self.owner)
        response = self.client.get("/")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("script-src 'self'", response["Content-Security-Policy"])
