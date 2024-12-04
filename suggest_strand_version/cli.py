import argparse
import importlib.metadata
import json
import logging
import os
import sys

from suggest_strand_version.api import suggest_strand_version
from suggest_strand_version.exceptions import StrandsException

RED = "\033[0;31m"
GREEN = "\033[0;32m"
NO_COLOUR = "\033[0m"


logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s | %(levelname)s | %(name)s] %(message)s",
    level=logging.INFO,
)


def main(argv=None):
    """Suggest the semantic version for an updated JSON schema. If this succeeds, exit successfully with an exit code of
    0; if it doesn't, exit with an exit code of 1.

    :return None:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "token",
        help="A Strands access token with permission to create a strand version for the given strand.",
    )
    parser.add_argument(
        "account",
        help="The account handle of the strand the new JSON schema should be compared against.",
    )
    parser.add_argument("name", help="The name of the strand the new JSON schema should be compared against.")
    parser.add_argument("path", help="The path to the JSON schema to to use (relative to the repository root).")

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=importlib.metadata.version("suggest-strand-version"),
        help="Print the version of the suggest-strand-version CLI.",
    )

    args = parser.parse_args(argv)

    with open(args.path) as f:
        json_schema = json.load(f)

    try:
        version, is_breaking, is_feature, is_patch = suggest_strand_version(
            token=args.token,
            account=args.account,
            name=args.name,
            json_schema=json_schema,
        )

    except StrandsException:
        print(f"{RED}SEMANTIC VERSION SUGGESTION FAILED.{NO_COLOUR}", file=sys.stderr)
        sys.exit(1)

    # Write outputs to GitHub outputs file for action.
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.writelines(
            [
                f"version={version}\n",
                f"is_breaking_change={is_breaking}\n",
                f"is_new_feature={is_feature}\n",
                f"is_patch_change={is_patch}\n",
            ]
        )

    print(f"{GREEN}SEMANTIC VERSION SUGGESTION SUCCEEDED:{NO_COLOUR} {version}.", file=sys.stderr)
    print(version)
    sys.exit(0)


if __name__ == "__main__":
    main()
