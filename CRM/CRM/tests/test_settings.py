import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_settings(extra_env):
    env = os.environ.copy()
    env.update(extra_env)
    command = [
        sys.executable,
        "-c",
        (
            "import json; from CRM import settings; "
            "print(json.dumps({"
            "'debug': settings.DEBUG, "
            "'hosts': settings.ALLOWED_HOSTS, "
            "'cors': settings.CORS_ALLOWED_ORIGINS, "
            "'db': settings.DATABASES['default'], "
            "'jwt_key_is_separate': settings.SIMPLE_JWT['SIGNING_KEY'] != settings.SECRET_KEY"
            "}, default=str))"
        ),
    ]
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class EnvironmentSettingsTests(SimpleTestCase):
    def test_production_requires_explicit_secret_keys(self):
        env = os.environ.copy()
        env.update({"DJANGO_ENV": "production"})
        env.pop("DJANGO_SECRET_KEY", None)
        env.pop("JWT_SIGNING_KEY", None)
        result = subprocess.run(
            [sys.executable, "-c", "from CRM import settings"],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_production_rejects_template_placeholder_keys(self):
        for django_key, jwt_key in [
            (
                "replace-with-a-long-random-django-secret",
                "replace-with-a-different-long-random-jwt-secret",
            ),
            ("short-key", "another-short-key"),
        ]:
            result = load_settings(
                {
                    "DJANGO_ENV": "production",
                    "DJANGO_SECRET_KEY": django_key,
                    "JWT_SIGNING_KEY": jwt_key,
                    "DB_ENGINE": "sqlite",
                }
            )
            self.assertNotEqual(result.returncode, 0)

    def test_postgresql_and_security_settings_are_loaded_from_environment(self):
        result = load_settings(
            {
                "DJANGO_ENV": "production",
                "DJANGO_SECRET_KEY": "django-secret-key-for-tests-with-at-least-fifty-characters-123",
                "JWT_SIGNING_KEY": "jwt-signing-key-for-tests-with-at-least-fifty-characters-456",
                "DJANGO_DEBUG": "false",
                "DJANGO_ALLOWED_HOSTS": "crm.example.com,api.example.com",
                "CORS_ALLOWED_ORIGINS": "https://crm.example.com",
                "DB_ENGINE": "postgresql",
                "POSTGRES_DB": "crm_test",
                "POSTGRES_USER": "crm_user",
                "POSTGRES_PASSWORD": "safe-test-password",
                "POSTGRES_HOST": "db",
                "POSTGRES_PORT": "5432",
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.strip())
        self.assertFalse(data["debug"])
        self.assertEqual(data["hosts"], ["crm.example.com", "api.example.com"])
        self.assertEqual(data["cors"], ["https://crm.example.com"])
        self.assertEqual(data["db"]["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(data["db"]["HOST"], "db")
        self.assertTrue(data["jwt_key_is_separate"])
