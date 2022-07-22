# Pyvarium

Pyvarium is a tool designed to help create environments which are managed by
both [Spack](github.com/spack/spack/) and
[Poetry](https://github.com/python-poetry/poetry).

It aims to help tackle the problem of long term reproducibility and portability
of software environments, especially in the area of scientific HPC, by combining
the ability of Spack to compile arbitrary software (as long as a package Spack
package has been written for it) and the ability of Poetry to create isolated
and versioned Python environments.

## Installation

Simplest installation is with [pipx](https://github.com/pypa/pipx):

```
pipx install pyvarium
```

## Quick Start

```sh
$ pyvarium --help
Usage: pyvarium [OPTIONS] COMMAND [ARGS]...

  Tool used to deploy computational environments managed with multiple tools
  like Poetry and Spack.

Options:
  --log-level [TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  Pick which level of output to show
                                  [default: INFO]

  -v, --verbose                   [default: 0]
  --install-completion            Install completion for the current shell.
  --show-completion               Show completion for the current shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.

Commands:
  install    Install the specified environment.
  modulegen  Generate modulefile to load the current environment
  new        Create a new environment - requires existing instances
  setup      Set up Spack/Poetry instances
  sync       Sync Spack-managed packages with Poetry pyproject.toml
```

Spack and Poetry are required by Pyvarium, both can be quickly set up with:

```
$ pyvarium setup spack /opt/pyvarium/spack-2022
$ pyvarium setup poetry /opt/pyvarium/poetry
```

Now a new environment can be created which uses those spack and poetry instances:

```
$ pyvarium new ./environment-demo /opt/pyvarium/poetry /opt/pyvarium/spack-2022
```

This creates a new directory `./environment-demo` which has Poetry
(`pyproject.toml`, `poetry.lock`) and Spack (`spack.yaml`, `spack.lock`)
environment specification files in it, as well as `activate` scripts which can
be used to activate the environment

In general setting up the environment must be done in a specific order, you must
install any python packages which have **external dependencies** via Spack
**first**, then run `pyvarium sync .`, and only then install any remaining
python packages via Poetry:

```
$ source activate.sh
$ spack add py-h5py py-numpy ...
$ spack install  # Once finished, run sync:
$ pyvarium sync .  # Then install additional packages via Poetry:
$ poetry add ...
```

The sync command will check for any python packages that were installed by Spack
and add them to `pyproject.toml` with a fixed version, so that Poetry does not
attempt to re-install, update, or modify them

Finally you an generate a module file with `pyvarium modulegen .`

## Usage

### `pyvarium setup`

Pyvarium needs Poetry and an existing Spack instance to work, for convenience a
`setup` command is included to help set these two up:

```sh
$ pyvarium setup --help
Usage: pyvarium setup [OPTIONS] COMMAND PREFIX [ARGS]...

  Set up Spack/Poetry instances

Options:
  --help  Show this message and exit.

Commands:
  poetry
  spack
```

For example:

```
$ pyvarium setup spack /opt/pyvarium/spack-2022
$ pyvarium setup poetry /opt/pyvarium/poetry
```

Would set up a spack instance at `/opt/pyvarium/spack-2022` and poetry at
`/opt/pyvarium/poetry`

### `pyvarium new`

Once instances are preset you can create a new environment:

```
$ pyvarium new --help
Usage: pyvarium new [OPTIONS] PATH POETRY_PREFIX SPACK_PREFIX COMMAND
                    [ARGS]...

  Create a new environment - requires existing instances

Options:
  PATH                            [required]
  POETRY_PREFIX                   [required]
  SPACK_PREFIX                    [required]
  --name TEXT
  --install-processes INTEGER     [default: 1]
  --skip-py-install / --no-skip-py-install
                                  [default: False]
  --force / --no-force            [default: False]
  --help                          Show this message and exit.

$ pyvarium new ./environment-demo /opt/pyvarium/poetry /opt/pyvarium/spack-2022
```

Creating a new environment requires a path to existing poetry and spack
instances, by default pyvarium will bootstrap new environments by installing
python into the spack instance if it is not already present

This can be time consuming, to skip this use the `--skip-py-install` flag

Once the environment is set up the directory will contain:

```
.
├── .venv
├── activate.fish
├── activate.sh
├── poetry.lock
├── poetry.toml
├── pyproject.toml
├── spack.lock
└── spack.yaml
```

You can source the `activate` files to load the environment and begin installing
software into the environment with standard Spack commands, followed by running
`pyvarium sync`, and then Poetry commands

### `pyvarium sync`

The sync command is the main purpose of pyvarium:

```
$ pyvarium sync .
```

Running it will first find any packages managed by Spack and then add them to
`pyproject.toml` with pinned versions so that Poetry does not attempt to modify
them

This way you can use Spack to install and manage complex dependencies which
require compilation, as well as python Packages which depend on external compiled
software, but you also retain the ability to install normal python packages
without having to create a Spack package for them

## TODO

- Work on creating a spack hook which runs sync after python packages are installed
- Add copying that hook into spack to `pyvarium setup spack`
- Work on hook that does git commits and pushes automatically
- Use named environments instead of anonymous ones
