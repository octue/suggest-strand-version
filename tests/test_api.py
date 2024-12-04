import json
import unittest
from unittest.mock import patch

from suggest_strand_version.api import _suggest_sem_ver, suggest_strand_version
from suggest_strand_version.exceptions import StrandsException


class TestSuggestSemanticVersion(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to get a semantic version suggestion without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"suggestSemVerViaToken": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                suggest_strand_version(
                    token="some-token",
                    account="some",
                    name="strand",
                    json_schema={"some": "schema"},
                )

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_with_valid_token(self):
        mock_response = {
            "suggestSemVerViaToken": {
                "suggestedVersion": "0.2.0",
                "isBreaking": False,
                "isFeature": True,
                "isPatch": False,
            }
        }

        json_schema_encoded = json.dumps({"some": "schema"})

        with patch("gql.Client.execute", return_value=mock_response) as mock_execute:
            version, is_breaking, is_feature, is_patch = _suggest_sem_ver(
                token="some-token",
                base="some/strand",
                proposed=json_schema_encoded,
            )

        self.assertEqual(version, "0.2.0")
        self.assertFalse(is_breaking)
        self.assertTrue(is_feature)
        self.assertFalse(is_patch)

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {"token": "some-token", "base": "some/strand", "proposed": json_schema_encoded},
        )
