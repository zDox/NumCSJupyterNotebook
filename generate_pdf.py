#!/usr/bin/env python3
import os
import sys
import subprocess
import nbformat
from typing import List
import uuid


class BuildConfig:
    def __init__(self):
        self.notebook_folder = "./notebooks"
        self.build_dir = "./build"
        self.merged_notebook = "book_merged.ipynb"
        self.output_pdf = "book.pdf"
        self.pdf_options = {
        }


config = BuildConfig()


def setup_build_dir():
    """Ensure build directory exists and is clean."""
    if os.path.exists(config.build_dir):
        for file in os.listdir(config.build_dir):
            os.remove(os.path.join(config.build_dir, file))
    else:
        os.makedirs(config.build_dir)


def execute_notebooks() -> List[str]:
    """Execute all notebooks and return list of executed notebook paths."""
    executed_notebooks = []

    for nb_file in sorted(os.listdir(config.notebook_folder)):
        if not nb_file.endswith(".ipynb"):
            continue

        input_path = os.path.join(config.notebook_folder, nb_file)
        output_filename = f"executed_{nb_file}"
        output_path = os.path.join(config.build_dir, output_filename)

        print(f"Executing {nb_file}...")
        try:
            subprocess.run([
                "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute", input_path,
                "--output", output_filename,
                "--output-dir", config.build_dir
            ], check=True)
            executed_notebooks.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error executing notebook {nb_file}: {e}", file=sys.stderr)

    return executed_notebooks


def merge_notebooks(notebook_paths: List[str]) -> str:
    """Merge executed notebooks into single notebook with unique cell IDs."""
    print("Merging notebooks...")
    merged_nb = nbformat.v4.new_notebook()

    for nb_path in notebook_paths:
        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Assign unique IDs to each cell to avoid duplicates
        for cell in nb.cells:
            cell['id'] = str(uuid.uuid4())[:8]

        merged_nb.cells.extend(nb.cells)

    merged_path = os.path.join(config.build_dir, config.merged_notebook)
    with open(merged_path, "w") as f:
        nbformat.write(merged_nb, f)
    return merged_path


def generate_pdf(notebook_path: str) -> None:
    """Convert notebook to PDF."""
    print("Converting to PDF...")
    try:
        cmd = [
            "jupyter", "nbconvert",
            notebook_path,
            "--to", "pdf",
            "--output-dir", ".",
            "--output", config.output_pdf
        ]
        subprocess.run(cmd, check=True)
        print(f"Done! PDF saved as {config.output_pdf}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        raise


def main():
    os.makedirs(config.notebook_folder, exist_ok=True)
    setup_build_dir()

    try:
        executed_paths = execute_notebooks()
        if not executed_paths:
            print("No notebooks were successfully executed!", file=sys.stderr)
            return 1

        merged_path = merge_notebooks(executed_paths)
        generate_pdf(merged_path)

        # Cleanup
        setup_build_dir()
        return 0
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())