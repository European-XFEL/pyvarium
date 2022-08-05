import json
import shutil
import subprocess
from pathlib import Path

import yaml
from loguru import logger

from pyvarium.installers import python_venv
from pyvarium.installers.base import Environment, Program


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

        if not hooks_dir.exists():
            raise Exception(f"Spack hooks directory does not exist: {hooks_dir}")

        shutil.copy(
            Path(__file__).parent / "python_venv.py",
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
        print(res)

        self.set_config({"spack": {"concretizer": {"unify": True}}})
        self.set_config(
            {
                "spack": {
                    "view": {
                        "default": {"root": str(view_path.resolve()), "link": "run"}
                    }
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

        return self.cmd("install", "--only-concrete", "--only", "package", "--no-add")

    def spec(self, spec: str) -> dict:
        res = self.cmd("spec", "-I", "--reuse", "--json", spec)
        return cmd_json_to_dict(res)

    def concretize(self):
        return self.cmd("concretize", "--reuse")

    def find(self) -> dict:
        res = self.cmd("find", "--json")
        return cmd_json_to_dict(res)

    def find_missing(self) -> dict:
        res = self.cmd(
            "find", "--show-concretized", "--deps", "--only-missing", "--json"
        )
        return cmd_json_to_dict(res)

    def find_python_packages(self):
        cmd = "PYTHONNOUSERSITE=True .venv/bin/python -m pip list --format json --disable-pip-version-check"
        res = subprocess.run(cmd, shell=True, capture_output=True, cwd=self.path)

        return json.loads(res.stdout.decode().strip())

    def get_config(self):
        return yaml.safe_load((self.path / "spack.yaml").read_text())

    def set_config(self, config: dict):
        current_config = self.get_config()
        new_config = recursive_dict_update(current_config, config)

        yaml.dump(new_config, (self.path / "spack.yaml").open("w"))
