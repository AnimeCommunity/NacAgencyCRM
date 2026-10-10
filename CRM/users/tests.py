from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken


User = get_user_model()


class UserSecurityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="StrongPass!2026", role="admin"
        )
        self.sales = User.objects.create_user(
            username="sales", password="StrongPass!2026", role="sales"
        )

    def test_public_registration_forces_sales_role(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "new-user",
                "email": "new@example.com",
                "password": "AnotherStrong!2026",
                "role": "admin",
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username="new-user")
        self.assertEqual(created.role, "sales")
        self.assertFalse(created.is_active)
        login_response = self.client.post(
            "/api/token/",
            {"username": "new-user", "password": "AnotherStrong!2026"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_cannot_manage_users(self):
        self.client.force_authenticate(self.sales)

        list_response = self.client.get("/api/users/")
        create_response = self.client.post(
            "/api/users/",
            {
                "username": "forged-admin",
                "password": "AnotherStrong!2026",
                "role": "admin",
            },
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(username="forged-admin").exists())

    def test_admin_user_creation_rejects_weak_password(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/users/",
            {"username": "weak", "password": "12345678", "role": "sales"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_admin_cannot_deactivate_or_demote_self(self):
        self.client.force_authenticate(self.admin)

        deactivate = self.client.patch(
            f"/api/users/{self.admin.id}/", {"is_active": False}, format="json"
        )
        demote = self.client.patch(
            f"/api/users/{self.admin.id}/", {"role": "sales"}, format="json"
        )

        self.assertEqual(deactivate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(demote.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.role, "admin")

    def test_admin_can_reactivate_inactive_user(self):
        inactive = User.objects.create_user(
            username="inactive", password="StrongPass!2026", role="sales", is_active=False
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/users/{inactive.id}/", {"is_active": True}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inactive.refresh_from_db()
        self.assertTrue(inactive.is_active)

    def test_login_access_token_contains_role_claim(self):
        response = self.client.post(
            "/api/token/",
            {"username": "sales", "password": "StrongPass!2026"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        claims = AccessToken(response.data["access"])
        self.assertEqual(claims["role"], "sales")

    def test_logout_blacklists_refresh_token(self):
        login_response = self.client.post(
            "/api/token/",
            {"username": "sales", "password": "StrongPass!2026"},
            format="json",
        )
        refresh = login_response.data["refresh"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        logout_response = self.client.post(
            "/api/logout/", {"refresh": refresh}, format="json"
        )
        refresh_response = self.client.post(
            "/api/token/refresh/", {"refresh": refresh}, format="json"
        )

        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
