[![PyPi version](https://img.shields.io/pypi/v/dm-cli)](https://pypi.org/project/dm-cli)
[![PyPi downloads](https://img.shields.io/pypi/dm/dm-cli)](https://pypi.org/project/dm-cli)
![Visitors](https://api.visitorbadge.io/api/visitors?path=equinor%2Fdm-cli&countColor=%23263759&style=flat)

# Data Modelling CLI Tool

## Requirements
This package requires Python >=3.11

## Installing
To install this CLI tool you can run the below command
```sh
$ pip3 install dm-cli
```

Alternatively, you clone this repo and then run this command from within the repository folder
```sh
$ pip3 install .
```

Both the above commands would install the package globally and `dm` will be available on your system.

## Usage

```txt
$ dm --help
Usage: dm [OPTIONS] COMMAND [ARGS]...

Options:
--version         Show the version and exit.
-t, --token TEXT  Token for authentication against DMSS.
-u, --url TEXT    URL to the Data Modelling Storage Service (DMSS).
-h, --help        Show this message and exit.

Commands:
create-lookup             Create a named Ui-/StorageRecipe-lookup-table...
ds                        Subcommand for working with data sources
entity                    Subcommand for working with entities
import-plugin-blueprints  Import blueprints from a plugin into the...
init                      Initialize the data sources and import all...
pkg                       Subcommand for working with packages
reset                     Reset all data sources (deletes and reuploads...
```

For each of the `commands` listed above, you can run `dm <COMMAND> --help` to see subcommand-specific help messages, e.g. `dm ds import --help` or `dm pkg --help`

### Expected directory structure
Certain commands expect a specific directory structure, such as the commands `dm reset`, `dm ds init`, and `dm ds reset`.
For these commands, the `path` argument must be the path to a directory with two subdirectories, `data_sources` and `data`.

```sh
$ tree app
app
├── data
  └── DemoApplicationDataSource
    ├── instances
│     └── demoApplication.json
|     └── models
|       └── DemoApplication.json
└── data_sources
    └── DemoApplicationDataSource.json
```

To add meta information to a package (for example to the models root package), a file with name "package.json" can be placed inside the folder.


### Supported reference syntax
The CLI tool will understand and resolve these kind of type reference schemas during import.
All values with one of these keys; `("type", "attributeType", "extends", "_blueprintPath_")` will be evaluated for resolution.

```bash
# URI - Full absolute path prefixed with protocol
dmss://datasource/package/entity
dmss://datasource/package/subfolder/entity

# Alias - Require dependencies to be defined somewhere in the source tree
ALIAS:packge/entity
ALIAS:entity

# Data Source - Relative from the destination data source
/package/entity
/package/subfolder/entity

# Package - Relative from the source package
entity
subfolder/entity

# Dotted - Relative from the file (UNIX directory traversal)
./../entity
../subfolder/entity
../../subfolder/entity
```

### General
Initialize the data sources

*i.e. import datasources and their packages*

```sh
$ dm ds init [<path>]
$ dm ds init app/
```
By default, the init command will also validate all entities that are uploaded to the database. This feature can be turned off with the flag `--no-validate-entities`:
```sh
$ dm ds init app/ --no-validate-entities
```

Reset all data sources

*i.e. delete all datasources and packages, before reuploading them*

```sh
# Reset all datasources and their packages
$ dm reset [<path>]
# By default, the `path` argument is set to the current working directory
$ dm reset
# Optionally specify a path to the directory containing data sources and data
$ dm reset app/
```

By default, the reset command will also validate all entities that are uploaded to the database. This feature can be turned off with the flag `--no-validate-entities`:
```sh
$ dm reset app --no-validate-entities
```

### Datasources
Import a datasource

```sh
# Import a datasource, where <path> is the path to a data source definition (JSON)
$ dm ds import <path>
$ dm ds import app/data_sources/DemoApplicationDataSource.json
```

Import all datasources

```sh
# Import all datasources found in the directory given by 'path'
$ dm ds import-all <path>
$ dm ds import-all app/data_sources
```

Reset a datasource

*i.e. reset the given data source, deleting all packages and reuploading them*

```sh
$ dm ds reset <data_source> [<path>]
# By default, the `path` argument is set to the current working directory
$ dm ds reset DemoApplicationDataSource
# Optionally specify a path to the directory containing data sources and data
$ dm ds reset DemoApplicationDataSource app/
```

### Plugin blueprints
Import blueprints from a plugin into the default plugin blueprint path (`system/Plugins/<plugin-name>)

```shell
dm import-plugin-blueprints ./node_modules/@development-framework/dm-core-plugins
```
> Note that this is the same as;
> `dm entity import ./node_modules/@development-framework/dm-core-plugins/blueprints/ system/Plugins/dm-core-plugins`


### Packages
Import a package
> Note that importing a package will delete any preexisting package with the same name, if present in DMSS

```sh
# Import the package <path> to the given data source
$ dm pkg import <path> <data_source>
# Import the package 'models' from app/data/DemoApplicationDataSource'
$ dm pkg import app/data/DemoApplicationDataSource/models DemoApplicationDataSource
```

Import all packages

```sh
# Import all packages found in the directory given by <path>
$ dm pkg import-all <path> <data_source>
# Import all packages in 'app/data/DemoApplicationDataSource'
$ dm pkg import-all app/data/DemoApplicationDataSource DemoApplicationDataSource
```


Exporting packages and single documents
```sh
# export document(s) by a given <data_source>/<path>
$ dm pkg export <data_source>/<path>
$ dm pkg export <data_source>/<path> <destination_path>
$ dm pkg export <data_source>/<path> <destination_path> --unpack

# Export all documents in 'DemoApplicationDataSource/models/CarPackage'
$ dm pkg export DemoApplicationDataSource/models/CarPackage
```

Optional arguments and flags:
<destination_path> : specifies where to save the downloaded file(s) on the local disk
unpack: whether or not to unpack the zip file

Delete a package

```sh
# Delete the package from the datasource in DMSS
$ dm pkg delete <data_source> <package_name>
# Delete the package 'models' from 'DemoApplicationDataSource'
$ dm pkg delete DemoApplicationDataSource models
```

Delete all packages
> Note that this will only delete packages which are present in the directory <path>, so any package present in DMSS but absent in the given directory will not be removed.

```sh
# Delete all packages found in the directory given by <path>
$ dm pkg delete-all <data_source> <path>
$ dm pkg delete-all DemoApplicationDataSource app/data/DemoApplicationDataSource
```

### Entities

Upload a single entity

```sh
$ dm entity import <local_path> <destination_path>
```

### Recipe Lookup
Create a named Ui-/StorageRecipe Lookup table from a package. Tell DMSS to look through a package,
gather all RecipeLinks, and create a named lookup from that. The lookup can be used to associate recipes with an application.

```sh
dm create-lookup myApplicationName path/To/A/Package/With/RecipeLinks
```

## Development
> You need to have DMSS running locally.

```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -e .
$ dm ds init
```

### Generating the DMSS API client
The DMSS API client, found in [`dm_cli/dmss_api/`](./dm_cli/dmss_api/), can be regenerated by running the script [`generate-dmss-api.sh`](./generate-dmss-api.sh). Note that an instance of DMSS must be running locally prior to executing the script.

```bash
./generate-dmss-api.sh
```

> NB: Due to incorrect import paths in the generated API client, you must do a search and replace after generating the new client. Replace all occurrences of '`from dmss_api`' with '`from dm_cli.dmss_api`' in all files under `dm_cli/dmss_api/`

### Testing

1. Install the dependencies: `pip3 install -r requirements.txt`
2. Install the dev dependencies: `pip3 install -r dev-requirements.txt`
3. Run the tests: `pytest`

## Feedback
Please feel free to leave feedback in issues/PRs.

<a id="Contributing"></a>
## :+1: Contributing
If you would like to contribute, please read our [Contribution guide](https://equinor.github.io/dm-docs/contributing/).
