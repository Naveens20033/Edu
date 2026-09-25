from rest_framework.test import APITestCase

from accounts.models import User


class AuthenticationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student.one",
            email="student.one@college.edu",
            password="correct-horse-42",
            role=User.Role.STUDENT,
        )

    def test_login_accepts_username_and_returns_profile(self):
        response = self.client.post("/api/auth/token/", {
            "username": "student.one", "password": "correct-horse-42",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role"], User.Role.STUDENT)
        self.assertEqual(response.data["user"]["id"], self.user.pk)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_accepts_email_case_insensitively(self):
        response = self.client.post("/api/auth/token/", {
            "username": "STUDENT.ONE@COLLEGE.EDU", "password": "correct-horse-42",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "student.one")

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post("/api/auth/token/", {
            "username": "student.one@college.edu", "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 401)

    def test_me_requires_authentication_and_returns_safe_profile(self):
        anonymous = self.client.get("/api/auth/me/")
        self.assertEqual(anonymous.status_code, 401)

        login = self.client.post("/api/auth/token/", {
            "username": "student.one", "password": "correct-horse-42",
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertNotIn("password", response.data)
