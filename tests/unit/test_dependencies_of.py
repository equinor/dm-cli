import unittest

from dm_cli.dmss_api.models.dependency import Dependency as ReportedDependency
from dm_cli.dmss_api.models.export_meta_response import ExportMetaResponse
from dm_cli.utils.reference import resolve_reference
from dm_cli.utils.utils import dependencies_of


class DependenciesOfTest(unittest.TestCase):
    """DMSS reports the dependencies a package inherits, and a reference can then be written
    against one of them. The reference resolver reads the address and protocol off a dependency,
    so what DMSS reports has to arrive in a form it can read."""

    @staticmethod
    def reported(**overrides) -> ExportMetaResponse:
        dependency = {
            "alias": "CORE",
            "type": "dmss://system/SIMOS/Dependency",
            "protocol": "dmss",
            "address": "system/SIMOS",
            "version": "1.0.0",
        }
        dependency.update(overrides)
        return ExportMetaResponse(dependencies=[ReportedDependency(**dependency)])

    def test_a_reported_dependency_can_resolve_a_reference_written_against_it(self):
        dependencies = dependencies_of(self.reported())

        self.assertEqual(
            "dmss://system/SIMOS/Blueprint",
            resolve_reference("CORE:Blueprint", dependencies, "test-DS", "root"),
        )

    def test_a_reported_dependency_is_found_by_its_alias(self):
        self.assertEqual(["CORE"], list(dependencies_of(self.reported())))

    def test_the_protocol_a_dependency_was_reported_with_is_kept(self):
        dependencies = dependencies_of(self.reported(protocol="http", address="example.com"))

        self.assertEqual(
            "http://example.com/Blueprint",
            resolve_reference("CORE:Blueprint", dependencies, "test-DS", "root"),
        )

    def test_a_package_without_dependencies_reports_none(self):
        self.assertEqual({}, dependencies_of(ExportMetaResponse()))
        self.assertEqual({}, dependencies_of(ExportMetaResponse(dependencies=[])))


if __name__ == "__main__":
    unittest.main()
