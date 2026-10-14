"""Offline checks for cloud configuration, lightweight probes, and same-origin frontend."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import httpx
from pydantic import ValidationError

from core.config import Settings
from core.database import Database
from main import create_app


class CloudSettingsTests(unittest.TestCase):
    def test_local_defaults_remain_sqlite_and_allow_local_frontend(self):
        settings = Settings(_env_file=None)
        self.assertEqual(settings.app_environment, "local")
        self.assertEqual(settings.database_backend, "sqlite")
        self.assertIn("http://localhost:5500", settings.cors_allowed_origins)

    def test_production_requires_durable_store_secure_cookie_and_provider_settings(self):
        with self.assertRaises(ValidationError):
            Settings(app_environment="production", _env_file=None)

    def test_production_rejects_wildcard_cors_and_sas_blob_urls(self):
        values = {
            "app_environment": "production",
            "database_backend": "cosmos",
            "openai_api_key": "test-openai-key",
            "cosmos_endpoint": "https://account.documents.azure.com:443/",
            "rag_index_blob_url": "https://account.blob.core.windows.net/rag/index.zip",
            "support_agent_api_key": "s" * 40,
            "cookie_secure": True,
            "cors_allowed_origins": "*",
            "_env_file": None,
        }
        with self.assertRaises(ValidationError):
            Settings(**values)
        values["cors_allowed_origins"] = ""
        values["rag_index_blob_url"] += "?sv=example"
        with self.assertRaises(ValidationError):
            Settings(**values)


class CloudProbeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "probe.sqlite3")
        self.app = create_app(self.database, Settings(_env_file=None))
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)
        self.temp_dir.cleanup()

    async def test_liveness_does_not_initialize_retrieval_or_contact_providers(self):
        with patch("main.get_retriever", side_effect=AssertionError("probe must stay lightweight")):
            response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    async def test_readiness_reports_database_and_catalogue_state(self):
        with patch("main.get_retriever") as get_retriever:
            get_retriever.return_value.get_count.return_value = 3
            response = await self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "products_loaded": 3})

    async def test_fastapi_serves_store_and_runtime_api_configuration(self):
        self.assertEqual((await self.client.get("/")).status_code, 200)
        self.assertIn("app-config.js", (await self.client.get("/index.html")).text)
        self.assertIn("apiBaseUrl", (await self.client.get("/app-config.js")).text)
        self.assertEqual((await self.client.get("/support.html")).status_code, 200)
        for page in ("shop.html", "product.html", "about.html", "shipping.html", "returns.html"):
            response = await self.client.get("/" + page)
            self.assertEqual(response.status_code, 200, page)


if __name__ == "__main__":
    unittest.main()
