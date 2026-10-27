import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings


class FrontendStaticViewTests(SimpleTestCase):
    def test_serves_exported_index_for_root_route(self):
        with tempfile.TemporaryDirectory() as directory:
            frontend_dir = Path(directory)
            (frontend_dir / "index.html").write_text(
                "<html><body>CRM local</body></html>", encoding="utf-8"
            )

            with override_settings(FRONTEND_DIST_DIR=frontend_dir):
                response = self.client.get("/")
                content = b"".join(response.streaming_content).decode("utf-8")
                response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn("CRM local", content)

    def test_serves_nested_exported_route_and_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            frontend_dir = Path(directory)
            route_dir = frontend_dir / "clients"
            asset_dir = frontend_dir / "_next" / "static"
            route_dir.mkdir(parents=True)
            asset_dir.mkdir(parents=True)
            (route_dir / "index.html").write_text("Clientes", encoding="utf-8")
            (asset_dir / "app.js").write_text("window.crm = true;", encoding="utf-8")

            with override_settings(FRONTEND_DIST_DIR=frontend_dir):
                route_response = self.client.get("/clients/")
                asset_response = self.client.get("/_next/static/app.js")
                route_content = b"".join(route_response.streaming_content).decode("utf-8")
                asset_content = b"".join(asset_response.streaming_content)
                route_response.close()
                asset_response.close()

        self.assertIn("Clientes", route_content)
        self.assertEqual(asset_response.status_code, 200)
        self.assertEqual(asset_content, b"window.crm = true;")

    def test_serves_next_page_payload_from_exported_directory_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            frontend_dir = Path(directory)
            payload_dir = frontend_dir / "register" / "__next.register"
            payload_dir.mkdir(parents=True)
            (payload_dir / "__PAGE__.txt").write_text(
                "next-page-payload", encoding="utf-8"
            )

            with override_settings(FRONTEND_DIST_DIR=frontend_dir):
                response = self.client.get(
                    "/register/__next.register.__PAGE__.txt"
                )
                content = b"".join(response.streaming_content).decode("utf-8")
                response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content, "next-page-payload")

    def test_missing_frontend_resource_returns_not_found(self):
        with tempfile.TemporaryDirectory() as directory:
            with override_settings(FRONTEND_DIST_DIR=Path(directory)):
                response = self.client.get("/missing/")

        self.assertEqual(response.status_code, 404)

    def test_encoded_parent_path_cannot_escape_frontend_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frontend_dir = root / "frontend"
            frontend_dir.mkdir()
            (root / "secret.txt").write_text("sensible", encoding="utf-8")

            with override_settings(FRONTEND_DIST_DIR=frontend_dir):
                response = self.client.get("/%2e%2e/secret.txt")

        self.assertEqual(response.status_code, 404)

    def test_windows_separator_parent_path_cannot_escape_frontend_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frontend_dir = root / "frontend"
            frontend_dir.mkdir()
            (root / "secret.txt").write_text("sensible", encoding="utf-8")

            with override_settings(FRONTEND_DIST_DIR=frontend_dir):
                response = self.client.get(r"/..\secret.txt")

        self.assertEqual(response.status_code, 404)
