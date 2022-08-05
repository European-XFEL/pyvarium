from pathlib import Path
from typing import Optional

import rtoml
from pydantic import BaseModel

from pyvarium import __version__


class ProgramConfig(BaseModel):
    executable: Path
    version: str


class PyProject(BaseModel):
    path: Path
    spack: ProgramConfig
    poetry: ProgramConfig

    @classmethod
    def load(cls, path: Optional[Path]) -> "PyProject":
        if path is None:
            path = cls.locate()

        pyproject = rtoml.load(path)

        try:
            pv = pyproject["tool"]["pyvarium"]
            spack = ProgramConfig(**pv["spack"])
            poetry = ProgramConfig(**pv["poetry"])
            return cls(path=path, spack=spack, poetry=poetry)
        except KeyError as e:
            raise RuntimeError(f"No/invalid pyvarium section in {path}") from e

    def write(self) -> None:
        if self.path.exists():
            pyproject = rtoml.loads(self.path.read_text())
        else:
            pyproject = {"tool": {"pyvarium": {}}}

        if pyproject.get("tool", {}).get("pyvarium", None):
            raise RuntimeError(f"pyvarium section already exists in {self.path}")

        pyproject["tool"]["pyvarium"] = {
            "version": __version__,
            "protected": False,
            "spack": {
                "executable": str(self.spack.executable),
                "version": str(self.spack.version),
            },
            "poetry": {
                "executable": str(self.poetry.executable),
                "version": str(self.poetry.version),
            },
        }

        self.path.write_text(rtoml.dumps(pyproject))

    @classmethod
    def locate(cls, cwd: Optional[Path] = None) -> Path:
        cwd = Path(cwd or Path.cwd())
        candidates = [cwd]
        candidates.extend(cwd.parents)

        for path in candidates:
            pyvarium_file = path / "pyproject.toml"

            if pyvarium_file.exists():
                return pyvarium_file

        raise RuntimeError(
            f"Pyvarium could not find a pyproject.toml file in {cwd} or its parents"
        )
