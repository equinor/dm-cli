import json
import unittest

from dm_cli.utils.resolve_local_ids import (
    dig_and_replace,
    resolve_local_ids_in_document,
    search_in_dict,
)


class ResolveLocalIdsTest(unittest.TestCase):
    def test_resolve_local_ids_in_document(self):
        with open("tests/unit/resolve_local_ids_test_data/carRentalCompany.json") as file:
            test_json = json.load(file)

        with open("tests/unit/resolve_local_ids_test_data/carRentalCompany.final.json") as file:
            expected = json.load(file)

        targets, references = search_in_dict(test_json, r"\^\.\$(\w+)", "_id", "^", True, {}, {})

        assert targets == {
            "Nested": "^",
            "12345": "^.cars[1](_id=12345)",
            "1234567": "^.cars[0](_id=1234567)",
            "54321": "^.cars[1](_id=54321)",
            "7654321": "^.cars[0](_id=7654321)",
            "accountant_drives_my_car": "^.accountant",
        }
        assert references == {
            "^.customers[0].car.address": "7654321",
            "^.customers[1].chauffeur.address": "accountant_drives_my_car",
        }

        dig_and_replace_result = dig_and_replace(targets, references, test_json)
        assert dig_and_replace_result == expected

        resolved_document = resolve_local_ids_in_document(test_json)
        assert resolved_document == expected
