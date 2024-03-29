import io
import json
import unittest
from pathlib import Path
from uuid import UUID
from zipfile import ZipFile

from dm_cli.dmss import ApplicationException
from dm_cli.domain import File
from dm_cli.package_tree_from_zip import package_tree_from_zip

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
    "MyPackage/package.json": {
        "name": "MyPackage",
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
    "MyPackage/WindTurbine.json": {
        "name": "WindTurbine",
        "type": "CORE:Blueprint",
        "extends": ["CORE:DefaultUiRecipes", "CORE:NamedEntity"],
        "_meta_": {
            "type": "CORE:Meta",
            "version": "0.0.1",
            "dependencies": [
                {
                    "type": "CORE:Dependency",
                    "alias": "SINTEF",
                    "address": "marine-models.sintef.com/Signals",
                    "version": "1.2.3",
                    "protocol": "http",
                }
            ],
        },
        "description": "",
        "attributes": [
            {
                "name": "Mooring",
                "type": "CORE:BlueprintAttribute",
                "attributeType": "Moorings/Mooring",
                "optional": True,
                "contained": False,
            },
            {
                "name": "Signal",
                "type": "CORE:BlueprintAttribute",
                "attributeType": "SINTEF:Default",
                "optional": True,
                "contained": False,
            },
        ],
    },
    "MyPackage/Moorings/Mooring.json": {
        "name": "Mooring",
        "type": "dmss://system/SIMOS/Blueprint",
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
    "MyPackage/Moorings/SpecialMooring.json": {
        "name": "SpecialMooring",
        "type": "CORE:Blueprint",
        "extends": ["CORE:DefaultUiRecipes", "Moorings/Mooring", "./Mooring"],
        "description": "",
        "attributes": [
            {
                "name": "Smallness",
                "type": "CORE:BlueprintAttribute",
                "description": "How small? Not that small really",
                "attributeType": "integer",
                "default": 1,
            },
            {
                "name": "ComplexTypeFromAnotherPacakge",
                "type": "/AnotherPackage/MyType",
                "description": "How big? Very",
                "attributeType": "integer",
            },
            {
                "name": "ComplexTypeFromAnotherPacakge",
                "type": "CORE:BlueprintAttribute",
                "description": "Type from parent folder",
                "attributeType": "../WindTurbine",
                "default": {
                    "name": "myTurbine",
                    "type": "../WindTurbine",
                    "description": "This is a wind turbine demoing uncontained relationships",
                },
            },
        ],
    },
    "MyPackage/myTurbine.json": {
        "name": "myTurbine",
        "type": "/WindTurbine",
        "description": "This is a wind turbine demoing uncontained relationships",
        "Mooring": {
            "_id": "apekatt",
            "type": "Moorings/Mooring",
            "name": "myTurbineMooring",
        },
    },
    "MyPackage/test_pdf.pdf": None,
    "MyPackage/Moorings/myTurbineMooring.json": {
        "_id": "fefff0e8-1581-4fa5-a9ed-9ab693e029ca",
        "name": "myTurbineMooring",
        "type": "Moorings/Mooring",
        "description": "",
        "Bigness": 10,
    },
    "MyPackage/A/SubFolder/FileNameDoesNotMatch.json": {
        "name": "myTurbine2",
        "type": "WindTurbine",
        "description": "This is a wind turbine demoing uncontained relationships",
        "Mooring": {
            "_id": "fefff0e8-1581-4fa5-a9ed-9ab693e029ca",
            "type": "../../Moorings/Mooring",
            "name": "myTurbineMooring",
        },
    },
    "MyPackage/B/myTurbine3.json": {
        "name": "myTurbine3",
        "type": "/WindTurbine",
        "description": "This is a wind turbine demoing uncontained relationships",
        "Mooring": {
            "_id": "fefff0e8-1581-4fa5-a9ed-9ab693e029ca",
            "type": "Moorings/Mooring",
            "name": "myTurbineMooring",
        },
    },
    "MyPackage/C/": None,
    "MyPackage/D/E/": None,
}

test_documents_with_dependency_conflict = {
    "MyPackage/package.json": {
        "name": "MyPackage",
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
                },
                {
                    "type": "CORE:Dependency",
                    "alias": "SINTEF",
                    "address": "marine-models.sintef.com/Signals",
                    "version": "1.2.3",
                    "protocol": "http",
                },
            ],
        },
    },
    "MyPackage/WindTurbine.json": {
        "name": "WindTurbine",
        "type": "CORE:Blueprint",
        "extends": ["CORE:DefaultUiRecipes", "CORE:NamedEntity"],
        "_meta_": {
            "type": "CORE:Meta",
            "version": "0.0.1",
            "dependencies": [
                {
                    "type": "CORE:Dependency",
                    "alias": "SINTEF",
                    "address": "marine-models.sintef.com/Signals/SpecialSignals",
                    "version": "3.2.1",
                    "protocol": "http",
                }
            ],
        },
        "description": "",
        "attributes": [
            {
                "name": "Mooring",
                "type": "CORE:BlueprintAttribute",
                "attributeType": "Moorings/Mooring",
                "optional": True,
                "contained": False,
            },
            {
                "name": "Signal",
                "type": "CORE:BlueprintAttribute",
                "attributeType": "SINTEF:Default",
                "optional": True,
                "contained": False,
            },
        ],
    },
}


class ImportPackageTest(unittest.TestCase):
    def test_package_tree_from_zip_with_relative_references(self):
        memory_file = io.BytesIO()
        with ZipFile(memory_file, mode="w") as zip_file:
            for path, document in test_documents.items():
                if Path(path).suffix == ".json":
                    zip_file.writestr(path, json.dumps(document).encode())
                elif Path(path).suffix == ".pdf":
                    zip_file.write(f"{Path(__file__).parent}/../test_data/{Path(path).name}", path)
                elif path[-1] == "/":
                    zip_file.write(Path(__file__).parent, path)

        memory_file.seek(0)

        root_package = package_tree_from_zip(
            destination="test_data_source/XRoot/",
            zip_package=memory_file,
        )
        folder_A = root_package.search("A")
        folder_Moorings = root_package.search("Moorings")
        myTurbineMooring = folder_Moorings.search("myTurbineMooring")
        mooringBlueprint = folder_Moorings.search("Mooring")
        folder_SubFolder = folder_A.search("SubFolder")
        myTurbine2 = folder_SubFolder.search("myTurbine2")

        assert mooringBlueprint["type"] == "dmss://system/SIMOS/Blueprint"

        assert myTurbine2["type"] == "dmss://test_data_source/XRoot/MyPackage/WindTurbine"
        assert isinstance(UUID(myTurbine2["Mooring"]["_id"]), UUID)
        assert myTurbine2["Mooring"]["type"] == "dmss://test_data_source/XRoot/MyPackage/Moorings/Mooring"
        assert myTurbine2["Mooring"]["_id"] == myTurbineMooring["_id"]

        windTurbine = root_package.search("WindTurbine")
        assert isinstance(UUID(windTurbine["_id"]), UUID)
        assert (
            windTurbine["attributes"][0]["attributeType"] == "dmss://test_data_source/XRoot/MyPackage/Moorings/Mooring"
        )
        assert (windTurbine["attributes"][1]["attributeType"]) == "http://marine-models.sintef.com/Signals/Default"
        assert windTurbine["extends"] == [
            "dmss://system/SIMOS/DefaultUiRecipes",
            "dmss://system/SIMOS/NamedEntity",
        ]
        assert windTurbine["_meta_"]["version"] == "0.0.1" and len(windTurbine["_meta_"]["dependencies"]) == 1

        specialMooring = folder_Moorings.search("SpecialMooring")
        assert len(specialMooring["extends"]) == 3
        assert specialMooring["extends"][2] == "dmss://test_data_source/XRoot/MyPackage/Moorings/Mooring"
        assert specialMooring["attributes"][1]["type"] == "dmss://test_data_source/AnotherPackage/MyType"
        assert specialMooring["attributes"][0]["default"] == 1
        assert (
            specialMooring["attributes"][2]["default"]["type"] == "dmss://test_data_source/XRoot/MyPackage/WindTurbine"
        )

        test_pdf = root_package.search("test_pdf.pdf")
        assert isinstance(test_pdf, File)
        assert test_pdf.content.name == "test_pdf.pdf"

    def test_package_tree_from_zip_with_dependency_conflict(self):
        memory_file = io.BytesIO()
        with ZipFile(memory_file, mode="w") as zip_file:
            for path, document in test_documents_with_dependency_conflict.items():
                if Path(path).suffix == ".json":
                    zip_file.writestr(path, json.dumps(document).encode())
                elif Path(path).suffix == ".pdf":
                    zip_file.write(f"{Path(__file__).parent}/../test_data/{Path(path).name}", path)
                elif path[-1] == "/":
                    zip_file.write(Path(__file__).parent, path)

        memory_file.seek(0)

        with self.assertRaises(ApplicationException):
            package_tree_from_zip(destination="test_data_source", zip_package=memory_file)
