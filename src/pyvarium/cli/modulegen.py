"""Install the specified environment."""

from pathlib import Path

import typer
from jinja2 import Template

from ..installers.pyvarium import Pyvarium

app = typer.Typer(help="Generate modulefile to load the current environment")

modulefile_template = Template(
    """#%Module 1.0
#
#  {{name}}
#

module-whatis  '{{name}} modulefile'
if { [ module-info mode load ] } {
{%- for path in paths %}
    prepend-path {{ path -}}
{% endfor %}
} elseif { [module-info mode remove] && ![module-info mode switch3] } {
{%- for path in paths %}
    remove-path {{path -}}
{% endfor %}
}
"""
)


@app.callback(invoke_without_command=True)
def main(
    path: Path = typer.Argument(...),
):
    path = Path(path).absolute()
    installer = Pyvarium.env_load(path)

    res = (
        installer.spack.cmd("env activate --sh .", no_env=True, prepend="env -i ")
        .stdout.decode()
        .split("\n")
    )

    env_vars = {
        l.strip("export ").split("=")[0]: l.strip("export ").split("=")[1]
        for l in res
        if l.startswith("export ")
    }

    paths = {k: ":".join(list(v.split(":"))).strip(":;") for k, v in env_vars.items()}

    print(
        modulefile_template.render(
            name="lol", paths=[f"{k} {v}" for k, v in paths.items()]
        ),
    )
