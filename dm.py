import click
from app.application import _load_app_settings
import concurrent.futures
import io
import json
import os
import traceback
from pathlib import Path
from zipfile import ZipFile
from app.dmss import dmss_api
import emoji
from zipfile import ZipFile

from app.import_package import package_tree_from_zip, import_package_tree, ApplicationException
from app.zip_all import zip_all

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class Portal(object):
    def __init__(self, dir=None, settings=None):
        self.dir = dir
        self.settings = settings

# https://click.palletsprojects.com/en/8.1.x/complex/
# https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/az
# https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/setup.py
# https://github.com/equinor/Quaid
# https://github.com/kanish671/ranpass
# https://medium.com/nerd-for-tech/how-to-build-and-distribute-a-cli-tool-with-python-537ae41d9d78

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--token", default="no-token", type=str)
@click.option('-dir', '--dir', type=str, help='Path to home directory')
@click.option('-url', '--dmss', default="http://localhost:8000", type=str,
              help='Url to Data Modelling Storage Service (DMSS)')
@click.pass_context
def cli(context, token: str, dir: str, dmss: str):
    dmss_api.api_client.default_headers["Authorization"] = "Bearer " + token
    dmss_api.api_client.configuration.host = dmss
    settings = _load_app_settings(dir)
    context.obj = Portal(dir, settings)
    click.echo(settings)


@cli.command()
@click.pass_context
def remove_application(context):
    click.echo("-------------- REMOVING OLD APPLICATION FILES ----------------")
    click.echo(
        f"Removing application specific files from the configured DMSS instance; {dmss_api.api_client.configuration.host}")

    def thread_function(settings: dict) -> bool:
        for package in settings.get("packages", []):
            data_source_alias, folder = package.split("/", 1)
            actual_data_source = next(
                (v for k, v in settings["dataSourceAliases"].items() if k == data_source_alias), data_source_alias
            )
            click.echo(f"Deleting package '{actual_data_source}/{folder}' from DMSS...")
            try:
                dmss_api.document_remove_by_path(actual_data_source, directory=folder)
            except Exception as error:
                if error.status == 404:
                    click.echo(emoji.emojize(f":warning: Could not find '{folder}' in DMSS..."))
                else:
                    raise error
        return True

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for result in executor.map(thread_function, context.obj.settings.values()):
            click.echo(result)
    click.echo("-------------- DONE ----------------")


@cli.command()
@click.argument("path")
def import_data_source(path: str):
    filename = Path(path).name
    click.echo(f"-------------- IMPORTING DATA SOURCE {filename} ----------------")
    with open(path) as file:
        document = json.load(file)
        try:
            dmss_api.data_source_save(document["name"], data_source_request=document)
            click.echo(f"Added data source '{document['name']}'")
        except (ApiException, KeyError) as error:
            if error.status == 400:
                click.echo(
                    emoji.emojize(
                        f":warning: Could not import data source '{filename}'. "
                        "A data source with that name already exists"
                    )
                )
            else:
                raise ImportError(f"Failed to import data source '{filename}': {error}")
    click.echo("_____ DONE importing data source _____")


@cli.command()
@click.pass_context
def init_application(context):
    click.echo("-------------- IMPORTING PACKAGES ----------------")

    APPS_DATASOURCE_SUBFOLDER = "data_sources"
    home = context.obj.dir

    def thread_function(settings: dict) -> None:
        app_directory_name = Path(settings["fileLocation"]).parent.name
        click.echo(f"Importing data for app '{settings['name']}'")
        click.echo("_____ importing data sources _____")
        ds_dir = f"{home}/{app_directory_name}/{APPS_DATASOURCE_SUBFOLDER}/"
        data_sources_to_import = []
        try:
            data_sources_to_import = os.listdir(ds_dir)
        except FileNotFoundError:
            click.echo(
                emoji.emojize(f":warning: No 'data_source' directory was found under '{ds_dir}'. Nothing to import...")
            )

        for filename in data_sources_to_import:
            context.invoke(import_data_source, path=f"{ds_dir}{filename}")

        click.echo("_____ DONE importing data sources _____")

        click.echo(f"_____ importing blueprints and entities {tuple(settings.get('packages', []))}_____")
        for package in settings.get("packages", []):
            data_source_alias, folder = package.split("/", 1)
            actual_data_source = settings["dataSourceAliases"].get(data_source_alias, data_source_alias)
            memory_file = io.BytesIO()
            with ZipFile(memory_file, mode="w") as zip_file:
                zip_all(
                    zip_file,
                    f"{home}/{app_directory_name}/data/{data_source_alias}/{folder}",
                    write_folder=True,
                )
            memory_file.seek(0)

            try:
                root_package = package_tree_from_zip(actual_data_source, folder, memory_file)
                # Import the package into the data source defined in _aliases_, or using the data_source folder name
                import_package_tree(root_package, actual_data_source)
            except ApplicationException as error:
                raise ApplicationException(error.body)
            except Exception as error:
                traceback.print_exc()
                raise Exception(f"Something went wrong trying to upload the package '{package}' to DMSS; {error}")
        click.echo(f"_____ DONE importing blueprints and entities {tuple(settings.get('packages', []))}_____")

        try:
            application_id = dmss_api.document_add_simple("DemoDS", settings)
            click.echo(f"Added application '{settings['name']}'")
            return application_id
        except (ApplicationException, KeyError) as error:
            if error.status == 400:
                click.echo(
                    emoji.emojize(
                        f":warning: Could not import application '{settings['name']}'. "
                        "A application with that name already exists"
                    )
                )
            else:
                raise ImportError(f"Failed to import application '{settings['name']}': {error}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        application_ids = []
        for result in executor.map(thread_function, context.obj.settings.values()):
            click.echo(result)
            application_ids.append(result)
        print(application_ids)

    try:
        portal_name = "portal"
        application_id = dmss_api.document_add_simple("DemoDS", {
            "type": "system/SIMOS/Portal",
            "name": portal_name,
            "applications": application_ids
        })
        click.echo(f"Added portal '{portal_name}'")
        return application_id
    except (ApplicationException, KeyError) as error:
        if error.status == 400:
            click.echo(
                emoji.emojize(
                    f":warning: Could not import portal '{portal_name}'. "
                    "A portal with that name already exists"
                )
            )
        else:
            raise ImportError(f"Failed to import portal '{portal_name}': {error}")

    click.echo(emoji.emojize("-------------- DONE ---------------- :check_mark_button:"))


@cli.command()
@click.pass_context
def reset_app(context):
    context.invoke(remove_application)
    context.invoke(init_application)


if __name__ == '__main__':
    cli()
