import os
import unittest
from unittest.mock import patch

from factory.providers.base import ModelProvider, ModelResponse
from factory.providers.fallback import FallbackProvider


class FlakyProvider(ModelProvider):
    name = "flaky"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, *, system=None):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("HTTP 503 service unavailable")
        return ModelResponse("recovered", self.name, "test-model")


class StatusCodeProvider(ModelProvider):
    name = "status-code"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, *, system=None):
        self.calls += 1
        error = RuntimeError("temporary upstream failure")
        error.status_code = 429
        raise error


class BrokenProvider(ModelProvider):
    name = "broken"

    def generate(self, prompt, *, system=None):
        raise RuntimeError("HTTP 403 forbidden")


class GoodProvider(ModelProvider):
    name = "good"

    def generate(self, prompt, *, system=None):
        return ModelResponse("fallback answer", self.name, "test-model")


class ProviderFallbackTests(unittest.TestCase):
    def test_retries_transient_failure_then_recovers(self):
        provider = FlakyProvider()
        with patch.dict(os.environ, {
            "AI_FACTORY_PROVIDER_RETRIES": "1",
            "AI_FACTORY_PROVIDER_RETRY_DELAY": "0",
        }, clear=False):
            result = FallbackProvider([provider]).generate("hello")
        self.assertEqual(result.text, "recovered")
        self.assertEqual(provider.calls, 2)

    def test_retries_from_structured_status_code(self):
        provider = StatusCodeProvider()
        with patch.dict(os.environ, {
            "AI_FACTORY_PROVIDER_RETRIES": "1",
            "AI_FACTORY_PROVIDER_RETRY_DELAY": "0",
        }, clear=False):
            with self.assertRaisesRegex(RuntimeError, "All configured AI providers failed"):
                FallbackProvider([provider]).generate("hello")
        self.assertEqual(provider.calls, 2)

    def test_skips_non_transient_failure_and_uses_next_provider(self):
        result = FallbackProvider([BrokenProvider(), GoodProvider()]).generate("hello")
        self.assertEqual(result.provider, "good")
        self.assertEqual(result.text, "fallback answer")

    def test_all_failures_remain_actionable(self):
        with self.assertRaisesRegex(RuntimeError, "All configured AI providers failed"):
            FallbackProvider([BrokenProvider()]).generate("hello")


if __name__ == "__main__":
    unittest.main()
