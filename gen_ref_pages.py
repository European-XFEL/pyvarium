"""Generate the code reference pages and navigation."""
from pathlib import Path

import mkdocs_gen_files

for path in sorted(Path("src").rglob("*.py")):
    if ".local" in str(path):
        continue

    module_path = path.relative_to("src").with_suffix("")
    doc_path = path.relative_to("src").with_suffix(".md")
    full_doc_path = Path("code-reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    full_doc_path = Path("code-reference") / full_doc_path.relative_to(
        "code-reference"
    )

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)
