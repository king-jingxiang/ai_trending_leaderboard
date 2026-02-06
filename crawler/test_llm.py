import unittest
from unittest.mock import MagicMock, patch
import os
import json
import logging
from crawler.llm import LLMClient

class TestLLMClient(unittest.TestCase):
    def setUp(self):
        # Reset env vars to avoid interference
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()
        # Mock OpenAI to prevent actual connection attempts during init if any
        self.openai_patcher = patch("crawler.llm.OpenAI")
        self.MockOpenAI = self.openai_patcher.start()
        self.client = LLMClient()

    def tearDown(self):
        self.env_patcher.stop()
        self.openai_patcher.stop()

    def test_init_defaults(self):
        """Test that default values match update_project_tags_v2.py defaults"""
        # Re-init to test defaults
        client = LLMClient()
        self.assertEqual(client.api_key, "sk-Empty")
        self.assertEqual(client.base_url, "http://127.0.0.1:3000/v1")
        self.assertEqual(client.model_name, "Qwen3-235B-A22B")

    def test_init_env_vars(self):
        """Test that environment variables are respected"""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "custom-key",
            "OPENAI_BASE_URL": "http://custom-url",
            "OPENAI_MODEL": "custom-model"
        }):
            client = LLMClient()
            self.assertEqual(client.api_key, "custom-key")
            self.assertEqual(client.base_url, "http://custom-url")
            self.assertEqual(client.model_name, "custom-model")

    def test_generate_tags_success(self):
        """Test successful generation with primary and secondary tags"""
        # Mock responses
        mock_response_primary = MagicMock()
        mock_response_primary.choices[0].message.content = json.dumps({
            "thinking_process": "Analysis...",
            "primary_tag": "Infrastructure & MLOps",
            "reason": "It's a tool."
        })

        mock_response_secondary = MagicMock()
        mock_response_secondary.choices[0].message.content = json.dumps({
            "thinking_process": "Sub-analysis...",
            "secondary_tags": ["Model Training", "Invalid Tag"]
        })

        # Setup mock client behavior
        self.client.client.chat.completions.create.side_effect = [
            mock_response_primary,
            mock_response_secondary
        ]

        repo_data = {
            "full_name": "test/repo",
            "description": "test desc",
            "readme": "test readme",
            "topics": ["ai"]
        }

        result = self.client.generate_tags(repo_data)

        # Verify calls
        self.assertEqual(self.client.client.chat.completions.create.call_count, 2)
        
        # Verify output structure
        self.assertEqual(result["primary_tags"], ["Infrastructure & MLOps"])
        # "Invalid Tag" should be filtered out
        self.assertEqual(result["secondary_tags"], ["Model Training"])

    def test_generate_tags_non_ai(self):
        """Test Non-AI classification"""
        mock_response_primary = MagicMock()
        mock_response_primary.choices[0].message.content = json.dumps({
            "thinking_process": "Not AI",
            "primary_tag": "Non-AI",
            "reason": "Not related."
        })

        self.client.client.chat.completions.create.return_value = mock_response_primary

        repo_data = {"full_name": "test/non-ai"}
        result = self.client.generate_tags(repo_data)
        
        self.assertEqual(result["primary_tags"], ["Non-AI"])
        self.assertEqual(result["secondary_tags"], [])
        self.assertEqual(self.client.client.chat.completions.create.call_count, 1)

    def test_generate_tags_invalid_json_fallback(self):
        """Test handling of invalid JSON response"""
        mock_response_bad = MagicMock()
        mock_response_bad.choices[0].message.content = "Not JSON"

        self.client.client.chat.completions.create.return_value = mock_response_bad

        repo_data = {"full_name": "test/bad"}
        result = self.client.generate_tags(repo_data)
        
        # Should return empty or fallback safe
        # Logic: if primary tag invalid (empty string from json error), check hierarchy. "" not in hierarchy -> Fallback to Non-AI if Non-AI in hierarchy, else empty.
        # "Non-AI" IS in hierarchy.
        # Wait, my code:
        # primary_tag = "" (from except)
        # if primary_tag not in TAG_HIERARCHY: ... if "Non-AI" in TAG_HIERARCHY: primary_tag = "Non-AI"
        self.assertEqual(result["primary_tags"], ["Non-AI"])
        self.assertEqual(result["secondary_tags"], [])

if __name__ == "__main__":
    unittest.main()
