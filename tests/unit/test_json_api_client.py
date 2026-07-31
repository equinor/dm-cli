import json
import re
import unittest

from dm_cli.dmss import JsonApiClient, dmss_api
from dm_cli.dmss_api.api_client import ApiClient
from dm_cli.dmss_api.models.error_response import ErrorResponse

"""
JsonApiClient replaces the generated 'deserialize' with a faster one for plain JSON. These tests pin
it to the generated behaviour, so that a regeneration of dm_cli/dmss_api which changes how values
are deserialized is caught here rather than in production.
"""

DOCUMENT = {
    "name": "myTurbine",
    "type": "WindTurbine",
    "power": 3.5,
    "active": True,
    "decommissioned": None,
    "tags": ["a", "b"],
    "mooring": {"name": "aMooring", "lines": [{"length": 1}, {"length": 2}]},
    "empty_list": [],
    "empty_dict": {},
}


class DeserializeTest(unittest.TestCase):
    """The generated deserializer cannot parse the 'Optional[...]' response types it emits itself.

    openapi-generator 7.24 describes a document response as "Dict[str, Optional[object]]", then
    looks 'Optional[object]' up as a model class and raises AttributeError. Since every endpoint
    that returns a document is typed that way, this would break document_get, export and search.
    """

    JSON = json.dumps(DOCUMENT)

    def deserialize(self, response_type, response_text=None):
        return JsonApiClient().deserialize(response_text or self.JSON, response_type, "application/json")

    def test_returns_documents_for_the_types_the_generator_emits(self):
        for response_type in ["object", "Dict[str, object]", "Dict[str, Optional[object]]"]:
            with self.subTest(response_type=response_type):
                self.assertEqual(self.deserialize(response_type), DOCUMENT)

    def test_the_generated_client_cannot_deserialize_a_document_response(self):
        # Guards the workaround: when this starts passing, the generator has been fixed upstream.
        with self.assertRaises(AttributeError):
            ApiClient().deserialize(self.JSON, "Dict[str, Optional[object]]", "application/json")

    def test_returns_lists_of_documents(self):
        text = json.dumps([DOCUMENT, DOCUMENT])
        self.assertEqual(self.deserialize("List[Dict[str, Optional[object]]]", text), [DOCUMENT, DOCUMENT])

    def test_documents_are_returned_verbatim(self):
        # Values must not be coerced. An earlier client turned every int into a float on the way out.
        document = self.deserialize("Dict[str, Optional[object]]", json.dumps({"width": 600, "power": 3.5}))

        self.assertIsInstance(document["width"], int)
        self.assertIsInstance(document["power"], float)

    def test_model_responses_still_go_through_the_generated_client(self):
        text = json.dumps({"status": 404, "type": "NotFoundException", "message": "gone", "debug": ""})

        self.assertIsInstance(self.deserialize("ErrorResponse", text), ErrorResponse)

    def test_dmss_api_uses_the_json_api_client(self):
        # The workaround only applies if the api is wired up with our client rather than the generated default.
        self.assertIsInstance(dmss_api.api_client, JsonApiClient)

    def test_every_response_type_the_generated_client_declares_is_classified(self):
        """A plain-JSON type must be handled here; anything else must reach the generated client."""
        from dm_cli.dmss import _PLAIN_JSON_RESPONSE_TYPE
        from dm_cli.dmss_api.api import default_api

        declared = set(re.findall(r"'[0-9X]+': \"([^\"]+)\"", open(default_api.__file__).read()))
        self.assertIn("Dict[str, Optional[object]]", declared, "the generated client no longer returns documents")

        for response_type in declared:
            handled_here = bool(_PLAIN_JSON_RESPONSE_TYPE.fullmatch(response_type))
            with self.subTest(response_type=response_type):
                self.assertEqual(handled_here, "object" in response_type)
