# Pyvarium

[![Tests](https://github.com/European-XFEL/pyvarium/actions/workflows/tests.yml/badge.svg)](https://github.com/European-XFEL/pyvarium/actions/workflows/tests.yml) | [![Docs](https://github.com/European-XFEL/pyvarium/actions/workflows/docs.yml/badge.svg)](https://european-xfel.github.io/pyvarium/)

Pyvarium is a tool designed to help create environments which are managed by [Spack](github.com/spack/spack/) and a pure python environment manager like [Pipenv](https://pipenv.pypa.io/en/latest/) or [Poetry](https://github.com/python-poetry/poetry).

It aims to help tackle the problem of long term reproducibility and portability of software environments, especially in the area of scientific HPC, by combining the ability of Spack to compile arbitrary software (as long as a package Spack package has been written for it) and flexibility of python environments.

## Installation

Simplest installation is with [pipx](https://github.com/pypa/pipx):

```shell
pipx install pyvarium
```

Note that Pyvarium is designed to **manage** Spack and python environments, so an existing spack installation as well as a supported backend (e.g. pipenv) is required for Pyvarium to run.

## Quick Start

```shell
$ pyvarium --help
Usage: pyvarium [OPTIONS] COMMAND [ARGS]...

Deploy mixed computational environments with dependencies and packages provided by Spack and Pipenv

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
  add                                Add packages via spack or pipenv.
  config                             Modify user settings for pyvarium.
  install                            Concretize and install an existing environment.
  modulegen                          Generate modulefile to load the environment.
  new                                Create a new combined Spack and Pipenv environment.
  sync                               Sync Spack-managed packages with Pipenv.
```

To create a new environment:

```
$ pyvarium new ./environment-demo
```

This creates a new directory `./environment-demo` which has Pipenv (`Pipfile`, `Pipfile.lock`) and Spack (`spack.yaml`, `spack.lock`) environment specification files in it. By default these will only specify `python` and `pip` as requirements.

In general setting up the environment should be done in a specific order, you must install any python packages which have **external dependencies** via Spack **first**, then install any required pure python packages via pipenv afterwards. Otherwise python packages with external dependencies will use their bundled binaries instead of whatever is provided via spack.


Installation of dependencies can be done with `pyvarium add {spack,pipenv}`, this command is a wrapper around the respective add/install commands which ensures that the dependencies specified by both programs remain in sync:

```shell
$ pyvarium add spack py-numpy py-h5py
$ pyvarium add pipenv extra-data
```

The above commands would install numpy and h5py via spack, compiling dependencies along the way, sync these packages with `Pipfile` so that pipenv is aware of what is already within the environment, and then install any specified packages via pipenv.

The environment can be activated as a normal venv with `source .venv/bin/activate`, or a module file can be created for it with with `pyvarium modulegen`.

## Usage

```shell
Usage: pyvarium [OPTIONS] COMMAND [ARGS]...

 Deploy mixed computational environments with dependencies and packages provided by Spack and Pipenv

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ --log-level                 [TRACE|DEBUG|INFO|WARNING|ERROR|C  Pick which level of output to show  │
│                             RITICAL]                           [default: LogLevel.info]            │
│ --install-completion                                           Install completion for the current  │
│                                                                shell.                              │
│ --show-completion                                              Show completion for the current     │
│                                                                shell, to copy it or customize the  │
│                                                                installation.                       │
│ --help                                                         Show this message and exit.         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────╮
│ add              Add packages via spack or pipenv.                                                 │
│ config           Modify user settings for pyvarium.                                                │
│ install          Concretize and install an existing environment.                                   │
│ modulegen        Generate modulefile to load the environment.                                      │
│ new              Create a new combined Spack and Pipenv environment.                               │
│ sync             Sync Spack-managed packages with Pipenv.                                          │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `config`

```shell
Usage: pyvarium config [OPTIONS] COMMAND [ARGS]...

 Modify user settings for pyvarium.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────╮
│ info   Show information about the current configuration.                                           │
│ list   List configuration.                                                                         │
│ set    Set a key value pair for configuration, e.g. `pyvarium set poetry_exec                      │
│        /opt/poetry/bin/poetry`.                                                                    │
│ unset  Remove a custom settings from configuration (this reverts to the default, to disable a      │
│        default set it to an empty string, e.g. `pyvarium set poetry_exec ""`).                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

`info` will show the absolute location of the configuration files being used, in the order they are loaded.

`list` shows the current configuration.

`set` can be used to set a key-value pair, and `unset` can be used to remove one. Setting and unsetting configurations can be performed at different scopes: `local` for the local directory (e.g. creating a `pyvarium.toml` file), `user` for the user configuration (`~/.config/pyvarium/settings.toml`), and `builtin` to modify the default configuration within the package.

The configuration is a TOML file containing the paths to the executables to be used by pyvarium, for example:

```toml
pipenv = "/home/roscar/.local/bin/pipenv"
pipx = "/home/roscar/.local/bin/pipx"
poetry = "/sbin/poetry"
spack = "/opt/spack"
```

By default, if an entry is not present in the file for one of these programs, it is automatically set to the path of `which $program`.

### `new`

```shell
Usage: pyvarium new [OPTIONS] PATH COMMAND [ARGS]...

 Create a new combined Spack and Pipenv environment.

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────╮
│ *    path      DIRECTORY  [default: None] [required]                                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `add`

```shell
Usage: pyvarium add [OPTIONS] COMMAND [ARGS]...

 Add packages via spack or pipenv.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────╮
│ pipenv                                                                                             │
│ spack                                                                                              │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
