from pathlib import Path
from typing import Optional

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
def main(
    path: Path = typer.Option(".", file_okay=False),
    name: Optional[str] = typer.Option("/".join(Path.cwd().parts[-2:])),
):
    path = Path(path).absolute()

    se = spack.SpackEnvironment(path)
    res = se.program.cmd("env", "activate", "--sh", str(path))

    commands = res.stdout.decode().split("\n")

    env_vars = {
        l.strip("export ").split("=")[0]: l.strip("export ").split("=")[1]
        for l in commands
        if l.startswith("export ")
    }

    paths = env_vars["PATH"].strip(";").split(":")
    if se.program.env["PATH"] in paths:
        paths.remove(se.program.env["PATH"])

    env_vars["PATH"] = ":".join(paths)
    env_vars["VIRTUAL_ENV"] = name

    paths = {
        k: ":".join(list(v.split(":"))).strip(";").strip(":")
        for k, v in env_vars.items()
    }

    modulefile = modulefile_template.render(
        name=name, paths=[f"{k} {v}" for k, v in paths.items()]
    )

    typer.echo(modulefile, color=False)
