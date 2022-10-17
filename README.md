[![PyPi version](https://img.shields.io/pypi/v/dm-cli)](https://pypi.org/project/dm-cli)
[![PyPi downloads](https://img.shields.io/pypi/dm/dm-cli)](https://pypi.org/project/dm-cli)
![Visitors](https://api.visitorbadge.io/api/visitors?path=equinor%2Fdm-cli&countColor=%23263759&style=flat)

# Data Modelling CLI Tool

### Requirements
This package requires Python 3.

### Installing
To install this CLI tool you can run the below command
```sh
$ pip3 install dm-cli
```

Alternatively, you clone this repo and then run this command from within the repository folder
```sh
$ pip3 install .
```

Both the above commands would install the package globally and `dm` will be available on your system.

### Usage

```sh
$ dm --help
Usage: python -m dm [OPTIONS] COMMAND [ARGS]...

Options:
  -t, --token TEXT  Token for authentication against DMSS.
  -u, --url TEXT    URL to the Data Modelling Storage Service (DMSS).
  -h, --help        Show this message and exit.

Commands:
  ds     Subcommand for working with data sources
  init   Initialize the data sources and import all packages.
  pkg    Subcommand for working with packages
  reset  Reset all data sources (deletes and reuploads packages)
```

For each of the `commands` listed above, you can run `dm <COMMAND> --help` to see subcommand-specific help messages, e.g. `dm ds import --help` or `dm pkg --help`

#### Expected directory structure
Certain commands expect a specific directory structure, such as the commands `dm reset`, `dm init`, and `dm ds reset`.
For these commands, the `path` argument must be the path to a directory with two subdirectories, `data_sources` and `data`.

```sh
$ tree app
app
├── data
│   └── DemoApplicationDataSource
│       ├── instances
│       │   └── demoApplication.json
│       └── models
│           └── DemoApplication.json
└── data_sources
    └── DemoApplicationDataSource.json
```

#### General
Initialize the data sources

*i.e. import datasources and their packages*

```sh
$ dm init [<path>]
# By default, the `PATH` argument is set to the current working directory
$ dm init
# Optionally specify a path to the directory containing data sources and data
$ dm init app/
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

#### Datasources
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

#### Packages
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

### Development
> You need to have DMSS running locally.

```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -e .
$ dm init
```

#### Testing

1. Install the dev dependencies: `pip3 install -r dev-requirements.txt`
2. Run the tests: `pytest`

### Feedback
Please feel free to leave feedback in issues/PRs.