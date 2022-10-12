import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Literal, Union, overload

import yaml
from loguru import logger

from pyvarium.installers.base import Environment, Program
from pyvarium.util import python_venv


def recursive_dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            r = recursive_dict_update(d.get(k, {}) if d is dict else {}, v)
            d[k] = r
        else:
            d[k] = v
    return d


def cmd_json_to_dict(cmd: subprocess.CompletedProcess) -> dict:
    return json.loads(cmd.stdout.decode())


class Spack(Program):
    def __post_init__(self):
        spack_dir = self.executable.parent.parent
        hooks_dir = spack_dir / "lib" / "spack" / "spack" / "hooks"

        if not hooks_dir.exists():  # pragma: no cover
            raise FileNotFoundError(
                f"Spack hooks directory does not exist: {hooks_dir}"
            )

        shutil.copy(
            python_venv.__file__,
            hooks_dir / "pyvarium_venv_activate.py",
        )


class SpackEnvironment(Environment):
    program: Spack

    def cmd(self, *args):
        return self.program.cmd("--env-dir", str(self.path), *args)

    def new(self, *, view_path: Path = Path(".venv")):
        commands = ["env", "create", "-d", str(self.path)]

        if view_path:
            if not view_path.is_absolute():
                view_path = self.path / view_path
            # Views are disabled here, as we set them manually via `set_config` to set
            # the link type to `run`
            commands.extend(["--without-view"])

        res = self.program.cmd(*commands)

        self.set_config({"spack": {"concretizer": {"unify": True}}})
        self.set_config(
            {
                "spack": {
                    "view": {
                        "default": {"root": str(view_path.resolve()), "link": "run"}
                    },
                    "concretizer": {"unify": True},
                }
            }
        )

        return res

    def init_view(self):
        res = self.cmd("env", "view", "regenerate")
        python_venv.setup_scripts(self.path / ".venv")
        return res

    def add(self, *packages):
        return self.cmd("add", *packages)

    def install(self):
        if not (self.path / "spack.lock").exists():
            logger.warning("No spack.lock file found, nothing will be installed")

        return self.cmd("install", "--only-concrete", "--no-add")

    # def spec(self, spec: str) -> dict:
    #     res = self.cmd("spec", "-I", "--reuse", "--json", spec)
    #     return cmd_json_to_dict(res)

    def concretize(self):
        return self.cmd("concretize", "--reuse")

    def find(self) -> dict:
        res = self.cmd("find", "--json")
        return cmd_json_to_dict(res)

    # def find_missing(self) -> dict:
    #     res = self.cmd(
    #         "find", "--show-concretized", "--deps", "--only-missing", "--json"
    #     )
    #     return cmd_json_to_dict(res)

    @overload
    def find_python_packages(self) -> List[dict]:
        ...

    @overload
    def find_python_packages(self, only_names: Literal[True]) -> List[str]:
        ...

    @overload
    def find_python_packages(self, only_names: Literal[False]) -> List[dict]:
        ...

    def find_python_packages(
        self, only_names: bool = False
    ) -> Union[List[str], List[dict]]:
        cmd = "PYTHONNOUSERSITE=True .venv/bin/python -m pip list --format json --disable-pip-version-check"
        res = subprocess.run(cmd, shell=True, capture_output=True, cwd=self.path)
        logger.debug(res)
        packages_json = res.stdout.decode().strip()

        if not packages_json:
            return []  # type: ignore

        packages_dict: List[dict] = json.loads(packages_json)

        if only_names:
            return [
                f"{p['name']}=={p['version']}"
                for p in packages_dict
                if p["name"] != "pip"
            ]
        else:
            return packages_dict

    def get_config(self) -> dict:
        return yaml.safe_load((self.path / "spack.yaml").read_text())

    def set_config(self, config: dict) -> None:
        current_config = self.get_config()
        new_config = recursive_dict_update(current_config, config)

        yaml.dump(new_config, (self.path / "spack.yaml").open("w"))
