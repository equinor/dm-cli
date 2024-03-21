# Data Modelling CLI Tool [![PyPi version](https://img.shields.io/pypi/v/dm-cli)](https://pypi.org/project/dm-cli) [![PyPi downloads](https://img.shields.io/pypi/dm/dm-cli)](https://pypi.org/project/dm-cli) ![Visitors](https://api.visitorbadge.io/api/visitors?path=equinor%2Fdm-cli&countColor=%23263759&style=flat)

CLI tool for working with [Data Modelling Storage Service](https://github.com/equinor/data-modelling-storage-service)

## Installing
> [!NOTE]
> Requires Python version >= 3.11

Install the tool via pip
```sh
$ pip3 install dm-cli
```

After a successful install, the program `'dm'` will be available in your python environment

## Usage

```txt
Usage: dm [OPTIONS] COMMAND [ARGS]...

Command Line Interface (CLI) tool for working with the Data Modelling Framework. This tool is mainly used to upload data source definitions, models and
entities, and creating RecipeLink-tables.

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --force               -f            Force the operation. Overwriting and potentially deleting data.                                                         │
│ --url                 -u      TEXT  URL to the Data Modelling Storage Service (DMSS). [default: http://localhost:5000]                                      │
│ --token               -t      TEXT  Token for authentication against DMSS. [default: no-token]                                                              │
│ --debug               -d            Print stack trace of suppressed exceptions                                                                              │
│ --version             -v            Print version and exit                                                                                                  │
│ --install-completion                Install completion for the current shell.                                                                               │
│ --show-completion                   Show completion for the current shell, to copy it or customize the installation.                                        │
│ --help                              Show this message and exit.                                                                                             │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ create-lookup              Create a named Ui-/StorageRecipe-lookup-table from all RecipeLinks in a package existing in DMSS (requires admin privileges).    │
│ ds                         Import and reset data sources                                                                                                    │
│ entities                   Import, delete, or validate entities and/or blueprints                                                                           │
│ export                     Export one or more entities.                                                                                                     │
│ import-plugin-blueprints   Import blueprints from a plugin into the standard location 'system/Plugins/<plugin-name>'.                                       │
│ reset                      Reset all data sources (deletes and re-uploads all packages to DMSS).                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

> [!TIP]
> For each of the `commands` listed above, you can run `dm <COMMAND> --help` to see subcommand-specific help messages, e.g. `dm ds import --help` or `dm pkg --help`

### Required directory structure
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
The CLI tool will understand and resolve the following address formats during import.


```bash
# URI - Full absolute path prefixed with protocol
dmss://datasource/package/entity
dmss://datasource/package/subfolder/entity
dmss://datasource/$123-456.attributeName

# Alias - Require dependencies to be defined somewhere in the source tree
ALIAS:package/entity
ALIAS:entity

# Data Source - Relative from the destination data source
/package/entity
/package/subfolder/entity
/$123-456.attributeName

# Package - Relative from the source package
entity
subfolder/entity

# Dotted - Relative from the file (UNIX directory traversal)
./../entity
../subfolder/entity
../../subfolder/entity
```

## Development

```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
# Install the package from local files in edit mode (-e)
$ pip3 install -e .
$ dm --help
```

### Testing

1. Install the dependencies: `pip3 install -r requirements.txt`
2. Install the dev dependencies: `pip3 install -r dev-requirements.txt`
3. Run the tests: `pytest`

## Feedback
Please feel free to leave feedback in issues/PRs.

## Contributing
If you would like to contribute, please read our [Contribution guide](https://equinor.github.io/dm-docs/contributing/).
