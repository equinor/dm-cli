import unittest
from pathlib import Path

from dm_cli.dmss import ApplicationException
from dm_cli.utils.reference import replace_relative_references
from dm_cli.utils.utils import concat_dependencies

"""
ROOT
 |
 |- WindTurbine.json
 |- myTurbine.json
 |- myPDF.json
 |- myNestedPDF.json
 |- myPDF.pdf
 |- Moorings
    |- Mooring.json
    |- SpecialMooring.json
    |- myTurbineMooring.json
|- A
    |- SubFolder
         |- myTurbine2.json
|- B
    |- myTurbine3.json
|- C # Empty folder
|- D
    |- E # Empty folder
"""

test_documents = {
    "MyRootPackage/package.json": {
        "name": "MyRootPackage",
        "type": "CORE:Package",
        "_meta_": {
            "type": "CORE:Meta",
            "version": "0.0.1",
            "dependencies": [
                {
                    "type": "CORE:Dependency",
                    "alias": "CORE",
                    "address": "system/SIMOS",
                    "version": "0.0.1",
                    "protocol": "dmss",
                }
            ],
        },
    },
    "MyRootPackage/Moorings/Mooring.json": {
        "name": "Mooring",
        "type": "CORE:Blueprint",
        "extends": ["CORE:DefaultUiRecipes", "CORE:NamedEntity"],
        "description": "",
        "attributes": [
            {
                "name": "Bigness",
                "type": "CORE:BlueprintAttribute",
                "description": "How big? Very",
                "attributeType": "integer",
            }
        ],
        "_meta_": {
            "type": "CORE:Meta",
            "version": "0.0.1",
            "dependencies": [
                {
                    "type": "CORE:Dependency",
                    "alias": "CORE",
                    "address": "system/SIMOS",
                    "version": "0.0.1",
                    "protocol": "dmss",
                }
            ],
        },
    },
    "MyRootPackage/Moorings/Mooring_no_meta.json": {
        "name": "Mooring_no_meta",
        "type": "CORE:Blueprint",
        "extends": ["CORE:DefaultUiRecipes", "CORE:NamedEntity"],
        "description": "",
        "attributes": [
            {
                "name": "Bigness",
                "type": "CORE:BlueprintAttribute",
                "description": "How big? Very",
                "attributeType": "integer",
            }
        ],
    },
}


class ImportEntityTest(unittest.TestCase):
    def test_replace_relative_references(self):
        src_path = Path("MyRootPackage/Moorings/Mooring.json")  # path
        dst_path = "MyRootPackage/Moorings"  # path_reference

        data_source_id, package = dst_path.split("/", 1)

        # Load the document
        document = test_documents[str(src_path)]
        dependencies = concat_dependencies(document.get("_meta_", {}).get("dependencies", []), {}, src_path.name)

        # Replace references
        prepared_document = {}
        for key, val in document.items():
            prepared_document[key] = replace_relative_references(
                key,
                val,
                dependencies,
                data_source_id,
                package,
                src_path.parent,
            )

        REFERENCE_PREFIX = "dmss://system/SIMOS"

        # Ensure the document's type has been replaced
        assert prepared_document["type"] == f"{REFERENCE_PREFIX}/Blueprint"

        # Ensure that references in 'extends' have been replaced
        assert prepared_document["extends"][0] == f"{REFERENCE_PREFIX}/DefaultUiRecipes"
        assert prepared_document["extends"][1] == f"{REFERENCE_PREFIX}/NamedEntity"

        # Ensure the attribute's type has been replaced
        assert prepared_document["attributes"][0]["type"] == f"{REFERENCE_PREFIX}/BlueprintAttribute"
        # Ensure the attribute's attributeType is not replaced, as it's a primitive
        assert prepared_document["attributes"][0]["attributeType"] == "integer"
        assert prepared_document["_meta_"]["type"] == "dmss://system/SIMOS/Meta"

    def test_replace_relative_references_no_meta(self):
        src_path = Path("MyRootPackage/Moorings/Mooring_no_meta.json")
        dst_path = "MyRootPackage/Moorings"

        data_source_id, package = dst_path.split("/", 1)

        # Load the document
        document = test_documents[str(src_path)]
        dependencies = concat_dependencies(document.get("_meta_", {}).get("dependencies", []), {}, src_path.name)

        with self.assertRaises(ApplicationException):
            # Replace references
            prepared_document = {}
            for key, val in document.items():
                prepared_document[key] = replace_relative_references(
                    key,
                    val,
                    dependencies,
                    data_source_id,
                    package,
                    src_path.parent,
                )
