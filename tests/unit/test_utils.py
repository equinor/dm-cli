import unittest

from dm_cli.utils.utils import get_root_packages_in_data_sources


class ImportEntityTest(unittest.TestCase):
    def test_get_root_package_content(self):
        path = "tests/test_data/test_app_dir_struct"
        datasource_contents = get_root_packages_in_data_sources(path)
        assert datasource_contents == {"DemoApplicationDataSource": ["models", "instances"]}
