from pathlib import Path
import pytest
from pyvarium.installers import Pyvarium


class TestPyvarium:
    @pytest.fixture(autouse=True, scope="class")
    def root(self, tmp_path_factory) -> Path:
        tmpdir = tmp_path_factory.mktemp("TestPyvarium")
        yield Path(tmpdir)

    @pytest.fixture(autouse=True, scope="class")
    def poetry_home(self, root) -> Path:
        yield root / "poetry"

    @pytest.fixture(autouse=True, scope="class")
    def spack_prefix(self, root) -> Path:
        yield root / "spack"

    @pytest.fixture(autouse=True, scope="class")
    def environment(self, root) -> Path:
        return root / "environment"

    def test_setup(self, poetry_home: Path, spack_prefix: Path):
        Pyvarium.setup(spack_prefix, poetry_home)

        assert (spack_prefix / "bin" / "spack").is_file()
        assert (poetry_home / "bin" / "poetry").is_file()

    def test_env_create(self, poetry_home: Path, spack_prefix: Path, environment: Path):
        pyvarium = Pyvarium.env_create(
            environment,
            protected=False,
            spack_executable=spack_prefix / "bin" / "spack",
            poetry_executable=poetry_home / "bin" / "poetry",
        )

    def test_env_load(self, environment: Path):
        pyvarium = Pyvarium.env_load(
            environment,
        )

    def test_constraint_sync(self, environment: Path):
        pyvarium = Pyvarium.env_load(
            environment,
        )

        pyvarium.sync_python_constraint()

    def test_packages_sync(self, environment: Path):
        pyvarium = Pyvarium.env_load(
            environment,
        )

        pyvarium.sync_python_packages()


class TestPyvariumIntegration:
    @pytest.fixture(autouse=True, scope="class")
    def root(self, tmp_path_factory) -> Path:
        tmpdir = tmp_path_factory.mktemp("TestPyvarium")
        yield Path(tmpdir)

    @pytest.fixture(autouse=True, scope="class")
    def poetry_home(self, root) -> Path:
        yield root / "poetry"

    @pytest.fixture(autouse=True, scope="class")
    def spack_prefix(self, cached_spack: Path) -> Path:
        executable = cached_spack / "bin" / "spack"
        assert executable.is_file(), "Spack executable not in cached instance"
        return cached_spack

    @pytest.fixture(autouse=True, scope="class")
    def environment(self, root) -> Path:
        return root / "environment"

    def test_setup(self, poetry_home: Path, spack_prefix: Path, environment: Path):
        Pyvarium.setup(spack_prefix, poetry_home)

        assert (spack_prefix / "bin" / "spack").is_file()
        assert (poetry_home / "bin" / "poetry").is_file()

        pyvarium = Pyvarium.env_create(
            environment,
            protected=False,
            spack_executable=spack_prefix / "bin" / "spack",
            poetry_executable=poetry_home / "bin" / "poetry",
        )

        pyvarium.spack.add("python@3.8.11", "py-pip")
        pyvarium.spack.add("py-pep8")
        pyvarium.spack.install()

        pyvarium.sync_python_packages()

        pyvarium.poetry.install_env()
