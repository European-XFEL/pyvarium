from pathlib import Path
from typing import Generator
import pytest

from pyvarium.installers.spack import SpackEnvironment


class TestSpack:
    se: SpackEnvironment

    @pytest.fixture(autouse=True, scope="class")
    def root(self, tmp_path_factory) -> Generator[Path, None, None]:
        tmpdir = tmp_path_factory.mktemp("TestSpack")
        yield Path(tmpdir) / "spack"

    @pytest.fixture(autouse=True)
    def environment(self, root):
        self.se = SpackEnvironment(root.parent / "environment")

    def test_new(self):
        self.se.new()
        assert (self.se.path / "spack.yaml").is_file()

    def test_init_view(self):
        self.se.init_view()
        assert (self.se.path / ".venv").is_dir()

    def test_setup_scripts_present(self):
        assert (self.se.path / ".venv" / "bin" / "activate").is_file()

    def test_config(self):
        # `set_config` is called during env creation, setting the following configs, so
        # this test implicitly checks settings configs as well
        config = self.se.get_config()
        assert config["spack"]["concretizer"]["unify"]
        assert config["spack"]["view"]["default"]["link"] == "run"

    def test_cmd(self):
        res = self.se.cmd("env", "st")
        assert str(self.se.path) in res.stdout.decode()

    def test_add(self):
        res = self.se.add("python", "py-pip", "py-numpy")
        assert "Adding python to environment" in res.stdout.decode()

    def test_install_no_lock(self):
        res = self.se.install()
        assert "no specs to install" in res.stdout.decode()

    def test_spec(self):
        res = self.se.spec("python")
        assert type(res) is dict
        assert res["spec"]["nodes"][0]["name"] == "python"

    def test_concretize(self):
        res = self.se.concretize()
        out = res.stdout.decode()
        assert "Concretized python" in out

    def test_install(self):
        res = self.se.install()
        assert f"Installing environment {str(self.se.path)}" in res.stdout.decode()

    def test_find_python_packages(self):
        res = self.se.find_python_packages()
        assert type(res) is list
        assert type(res[0]) is dict
        assert any(r["name"] == "numpy" for r in res)

    def test_find_python_packages_only_names(self):
        res = self.se.find_python_packages(only_names=True)
        assert type(res) is list
        assert type(res[0]) is str
        assert any("numpy" in r for r in res)
