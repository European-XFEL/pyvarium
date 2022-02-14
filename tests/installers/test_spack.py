from pathlib import Path
import pytest

from pyvarium.installers.spack import Spack


class TestSpack:
    @pytest.fixture(autouse=True, scope="class")
    def root(self, tmp_path_factory) -> Path:
        tmpdir = tmp_path_factory.mktemp("TestSpack")
        root = Path(tmpdir) / "spack"
        yield root

    @pytest.fixture(autouse=True, scope="class")
    def environment(self, root) -> Path:
        return root.parent / "environment"

    def test_setup(self, root: Path):
        Spack.setup(root, force=False)
        assert (root / "bin" / "spack").is_file()

    def test_setup_no_force(self, root: Path):
        with pytest.raises(FileExistsError):
            Spack.setup(root, force=False)

    def test_env_create(self, root: Path, environment: Path):
        Spack.env_create(environment, executable=root / "bin" / "spack")

        assert (
            environment / ".venv"
        ).is_dir(), f"view not found at {environment / '.venv'}"

        assert (
            environment / "spack.yaml"
        ).is_file(), f"config not found at {environment / 'spack.yaml'}"

    def test_env_configs(self, root: Path, environment: Path):
        spack = Spack.env_load(environment, executable=root / "bin" / "spack")
        spack.cmd("compiler find")
        spack.cmd("compiler list")

        with spack.config() as config:
            assert config.spack.concretization == "together"
            assert config.spack.view == str(environment / ".venv")

    def test_env_add(self, root: Path, environment: Path):
        spack = Spack.env_load(environment, executable=root / "bin" / "spack")
        spack.add("python@3.8.11", "py-pip")

        with spack.config() as config:
            assert "python@3.8.11" in config.spack.specs
            assert "py-pip" in config.spack.specs

        assert not (environment / "spack.lock").is_file()

    def test_env_concretize(self, root: Path, environment: Path):
        spack = Spack.env_load(environment, executable=root / "bin" / "spack")
        spack.concretize()

        assert (environment / "spack.lock").is_file()

    def test_version(self, root: Path, environment: Path):
        spack = Spack.env_load(environment, executable=root / "bin" / "spack")
        assert spack.version


class TestSpackIntegration:
    @pytest.fixture(autouse=True, scope="class")
    def root(self, cached_spack: Path) -> Path:
        executable = cached_spack / "bin" / "spack"
        assert executable.is_file(), "Spack executable not in cached instance"
        return cached_spack

    @pytest.fixture(autouse=True, scope="class")
    def environment(self, tmp_path_factory) -> Path:
        yield tmp_path_factory.getbasetemp() / "environment"

    def test_env_install(self, root: Path, environment: Path):
        spack = Spack.env_create(environment, executable=root / "bin" / "spack")

        spack.add("python@3.8.11", "py-pip")
        spack.concretize()
        spack.install()

    def test_python_present(self, root: Path, environment: Path):
        assert (environment / ".venv" / "bin" / "python3").is_file()
        assert (environment / ".venv" / "bin" / "pip3").is_file()

    def test_env_install_parallel(self, root: Path, environment: Path):
        spack = Spack.env_create(environment, executable=root / "bin" / "spack")

        spack.add("py-numpy")
        spack.concretize()
        spack.install(processes=4)

        # Check if numpy is available
        assert (
            environment / ".venv" / "lib" / "python3.8" / "site-packages" / "numpy"
        ).is_dir()
