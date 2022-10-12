from pathlib import Path

import typer
from jinja2 import Template

from pyvarium.installers import spack

app = typer.Typer(help="Generate modulefile to load the environment.")

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
def main(path: Path = typer.Option(".", file_okay=False)):
    path = Path(path).absolute()

    se = spack.SpackEnvironment(path)
    res = se.program.cmd("env", "activate", "--sh", ".")

    commands = res.stdout.decode().split("\n")

    env_vars = {
        l.strip("export ").split("=")[0]: l.strip("export ").split("=")[1]
        for l in commands
        if l.startswith("export ")
    }

    env_vars.pop("PYTHONPATH", None)

    env_vars["VIRTUAL_ENV"] = f"{path.parent.name}/{path.name}"

    paths = {k: ":".join(list(v.split(":"))).strip(":;") for k, v in env_vars.items()}

    print(
        modulefile_template.render(
            name=path.name, paths=[f"{k} {v}" for k, v in paths.items()]
        ),
    )
