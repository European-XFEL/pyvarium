from contextlib import contextmanager
from pathlib import Path

import rich.repr
from box import Box
from loguru import logger
from poetry.core.pyproject import PyProjectTOML
from poetry.core.semver import Version, VersionRange, VersionTypes, parse_constraint
from tomlkit.api import table as toml_table

from .. import __version__
from .poetry import Poetry
from .spack import Spack


@rich.repr.auto
class Pyvarium:
    def __init__(
        self,
        env_path: Path,
        protected: bool = False,
        force: bool = False,
    ) -> None:
        self.env_path = env_path
        self.force = force
        self.protected = protected

        self.spack: Spack
        self.poetry: Poetry

        logger.trace(f"Created: {self}")

    @contextmanager
    def config(self):
        pyproject = PyProjectTOML((self.env_path / "pyproject.toml"))

        try:
            yield pyproject.data
        finally:
            pyproject.save()

    @property
    def _config(self) -> Box:
        return Box.from_toml(
            (self.env_path / "pyproject.toml").read_text(),
            frozen_box=True,
            default_box=False,
        )

    @classmethod
    def env_create(
        cls,
        env_path: Path,
        poetry: Poetry,
        spack: Spack,
        protected: bool = False,
        force: bool = False,
    ) -> "Pyvarium":
        pyvarium = cls(env_path, protected, force)

        if pyvarium.protected and force:
            logger.warning("`force` and `protected` are both set, disabling `force`")
            force = False

        pyvarium.protected = protected

        with pyvarium.config() as config:
            pv = config.get("tool", toml_table())["pyvarium"] = toml_table()
            pv["version"] = __version__
            pv["protected"] = pyvarium.protected
            pv["spack"] = toml_table()
            pv["spack"]["executable"] = str(spack.installer_config.executable)  # type: ignore
            pv["spack"]["version"] = spack.version  # type: ignore
            pv["poetry"] = toml_table()
            pv["poetry"]["executable"] = str(poetry.installer_config.executable)  # type: ignore
            pv["poetry"]["version"] = poetry.version.lower().replace(  # type: ignore
                "poetry version ", ""
            )

        cls.spack = spack
        cls.poetry = poetry

        spack_share = spack.installer_config.prefix / "share" / "spack"

        activate_script_sh = [
            f"source {spack_share / 'setup-env.sh'}",
            f"spack env activate {env_path}",
        ]
        (env_path / "activate.sh").write_text("\n".join(activate_script_sh))

        activate_script_fish = [
            f"source {spack_share / 'setup-env.fish'}",
            f"spack env activate {env_path}",
        ]
        (env_path / "activate.fish").write_text("\n".join(activate_script_fish))

        return pyvarium

    @classmethod
    def env_load(
        cls,
        env_path: Path,
    ) -> "Pyvarium":
        pyvarium = cls(env_path)

        with pyvarium.config() as config:
            if "pyvarium" not in config["tool"].keys():  # type: ignore
                raise KeyError(
                    f"{env_path} has no [tool.pyvarium] section, has the pyvarium"
                    f"environment been set up?"
                )

            pv = config["tool"]["pyvarium"]  # type: ignore

            pyvarium.protected = pv["protected"]  # type: ignore

            pyvarium.spack = Spack.env_load(
                env_path,
            )

            pyvarium.poetry = Poetry.env_load(
                env_path,
            )

        return pyvarium

    def sync_python_constraint(self):
        poetry_constraint = parse_constraint(
            self._config["tool"]["poetry"]["dependencies"]["python"]
        )

        spack_constraint = "*"
        for spec in self.spack._config["spack"].get("specs", {}):  # type: ignore
            if spec.startswith("python@"):
                spack_constraint = spec.split("@")[1]
        spack_constraint = parse_constraint(spack_constraint)

        python_min, python_max = _check_python_version_constraints(
            poetry_constraint, spack_constraint
        )

        spack_spec_python = f"python@{python_min}:{python_max}"
        if spack_spec_python not in self.spack._config.spack.specs:  # type: ignore
            self.spack.cmd(f"add {spack_spec_python}")
        else:
            logger.debug(
                f"not running spack cmd `add {spack_spec_python}`, already present"
            )

    def sync_python_packages(self):
        spack_python_packages = self.spack.list_python_packages()

        logger.debug(spack_python_packages)

        new_packages = []

        if spack_python_packages and spack_python_packages != [""]:
            for package in spack_python_packages:
                package_name = package["name"]
                package_version = package["version"]

                poetry_package_names = self._config.tool.poetry.dependencies.keys()  # type: ignore

                if package_name.capitalize() in poetry_package_names:
                    package_name = package_name.capitalize()

                poetry_package_version = self._config.tool.poetry.dependencies.get(  # type: ignore
                    package_name
                )

                if poetry_package_version != package_version:
                    new_packages.append(f"{package_name}@{package_version}")
                else:
                    logger.debug(f"{package} already in poetry")

        if new_packages:
            logger.info(f"Adding `{new_packages}` to poetry as spack dependency")
            self.poetry.add(new_packages, lock=True)


def _check_python_version_constraints(
    poetry_constraint: VersionTypes, spack_constraint: VersionTypes
):
    if poetry_constraint.allows(spack_constraint):  # type: ignore
        intersect = poetry_constraint.intersect(spack_constraint)
    elif spack_constraint.allows(poetry_constraint):  # type: ignore
        intersect = spack_constraint.intersect(poetry_constraint)
    else:  # type: ignore
        logger.critical(
            f"Spack constraint {spack_constraint} does not allow poetry "
            f"version {poetry_constraint}"
        )
        raise ValueError("Constraint not satisfiable")

    if isinstance(intersect, Version):
        return intersect.min, intersect.next_breaking
    elif isinstance(intersect, VersionRange):
        return intersect.min, intersect.max
    else:
        logger.critical(
            f"Unsupported version range {intersect} for spack constraint {spack_constraint}",
        )
        raise ValueError("Constraint not satisfiable")
