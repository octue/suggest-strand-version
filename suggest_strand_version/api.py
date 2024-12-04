import json
import logging
import os

import gql
from gql.transport.requests import RequestsHTTPTransport

from suggest_strand_version.exceptions import StrandsException

STRANDS_API_URL = os.environ.get("STRANDS_API_URL", "https://api.octue.com/graphql/")

logger = logging.getLogger(__name__)
transport = RequestsHTTPTransport(url=STRANDS_API_URL)
client = gql.Client(transport=transport, fetch_schema_from_transport=True)


def suggest_strand_version(token, account, name, json_schema):
    """Suggest the semantic version for an updated JSON schema.

    :param str token: a Strands access token with permission to add a new strand version to a specific strand
    :param str account: the handle of the account the strand belongs to
    :param str name: the name of the strand
    :param dict json_schema: the JSON schema to add to the strand as a strand version
    :return (str, bool, bool, bool):
    """
    suid = f"{account}/{name}"

    version, is_breaking, is_feature, is_patch = _suggest_sem_ver(
        token=token,
        base=suid,
        proposed=json.dumps(json_schema),
    )

    return version, is_breaking, is_feature, is_patch


def _suggest_sem_ver(token, base, proposed):
    """Query the GraphQL endpoint for a suggested semantic version for the proposed schema relative to a base schema.

    :param str token: a Strands access token with any scope
    :param str base: the base schema as a strand unique identifier (SUID) of an existing strand
    :param str proposed: the proposed schema as a JSON-encoded string
    :raises suggest_strand_version.exceptions.StrandsException: if the query fails for any reason
    :return (str, bool, bool, bool): the suggested semantic version for the proposed schema and whether it represents a breaking, feature, or patch change
    """
    parameters = {"token": token, "base": base, "proposed": proposed}

    query = gql.gql(
        """
        mutation suggestSemVerViaToken(
            $token: String!,
            $base: String!,
            $proposed: String!,
        ){
            suggestSemVerViaToken(token: $token, base: $base, proposed: $proposed) {
                ... on VersionSuggestion {
                    suggestedVersion
                    isBreaking
                    isFeature
                    isPatch
                }
                ... on VersionSuggestionError {
                    type
                    message
                }
                ... on OperationInfo {
                    messages {
                        kind
                        message
                        field
                        code
                    }
                }
            }
        }
        """
    )

    logger.info("Getting suggested semantic version...")
    response = client.execute(query, variable_values=parameters)["suggestSemVerViaToken"]

    if "messages" in response or "message" in response:
        raise StrandsException(response.get("messages") or response.get("message"))

    if response["isBreaking"]:
        change_type = "breaking change"
    elif response["isFeature"]:
        change_type = "new feature"
    else:
        change_type = "patch change"

    logger.info(
        "The suggested semantic version is %s. This represents a %s.",
        response["suggestedVersion"],
        change_type,
    )

    return response["suggestedVersion"], response["isBreaking"], response["isFeature"], response["isPatch"]
