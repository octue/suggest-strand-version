import os
import tempfile
import unittest
from unittest.mock import mock_open, patch

from suggest_strand_version import cli
from suggest_strand_version.exceptions import StrandsException


class TestCLI(unittest.TestCase):
    def test_with_failed_suggestion(self):
        """Test that the exit code is 1 if suggesting fails."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("suggest_strand_version.cli.suggest_strand_version", side_effect=StrandsException):
                with patch("sys.stderr") as mock_stderr:
                    with self.assertRaises(SystemExit) as e:
                        cli.main(
                            [
                                "some-token",
                                "some",
                                "strand",
                                "non-existent-path.json",
                            ]
                        )

        self.assertEqual(e.exception.code, 1)

        message = mock_stderr.method_calls[0].args[0]
        self.assertIn("SEMANTIC VERSION SUGGESTION FAILED.", message)

    def test_with_successful_suggestion(self):
        """Test that the exit code is 0 if suggesting succeeds and that the mutation is called with the correct
        arguments.
        """
        mock_suggest_strand_version = patch(
            "suggest_strand_version.cli.suggest_strand_version",
            return_value=("0.2.0", False, True, False),
        )

        with patch("builtins.open", mock_open(read_data='{"some": "schema"}')):
            with mock_suggest_strand_version as mock_suggest_strand_version:
                with tempfile.NamedTemporaryFile() as temporary_file:
                    with patch.dict(os.environ, {"GITHUB_OUTPUT": temporary_file.name}):
                        with patch("sys.stderr") as mock_stderr:
                            with patch("sys.stdout") as mock_stdout:
                                with self.assertRaises(SystemExit) as e:
                                    cli.main(
                                        [
                                            "some-token",
                                            "some",
                                            "strand",
                                            "non-existent-path.json",
                                        ]
                                    )

        mock_suggest_strand_version.assert_called_with(
            token="some-token",
            account="some",
            name="strand",
            json_schema={"some": "schema"},
        )

        self.assertEqual(e.exception.code, 0)

        message = mock_stderr.method_calls[0].args[0]
        self.assertIn("SEMANTIC VERSION SUGGESTION SUCCEEDED:", message)
        self.assertIn("0.2.0", message)

        message = mock_stdout.method_calls[0].args[0]
        self.assertEqual(message, "0.2.0")
