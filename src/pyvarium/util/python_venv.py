import venv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Context:
    """Subsection of the context provided by venv.EnvBuilder.ensure_directories"""

    bin_path: str
    bin_name: str
    env_dir: str
    env_name: str
    prompt: str
    env_exe: str


def setup_scripts(spack_view_path: Path):
    spack_view_path = spack_view_path.absolute()
    eb = venv.EnvBuilder()
    context = Context(
        env_dir=str(spack_view_path),
        env_name=str(spack_view_path.parent.parent),
        prompt=f"({spack_view_path.parent.parent.name}) ",
        bin_path=str(spack_view_path / "bin"),
        bin_name="bin",
        env_exe=str(spack_view_path / "bin" / "python"),
    )

    eb.setup_scripts(context)  # type: ignore


def post_env_write(env):  # pragma: no cover
    # The scripts are written every time an env event occurs, as they almost always
    # overwrite/delete the existing scripts
    if "default" in env.views:
        env_path = Path(env.views["default"].root)
        if env_path.exists() and not (env_path / "bin" / "activate").exists():
            setup_scripts(env_path)
