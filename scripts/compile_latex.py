import subprocess
import os
import sys

# Bash
# python compile_latex.py actionable_model_article.tex

def compile_latex(tex_file, runs=2, clean_aux=True):
    """
    Compile a LaTeX file into PDF using pdflatex.

    Parameters:
    - tex_file (str): Path to the .tex file
    - runs (int): Number of compilation runs (default=2 for references)
    - clean_aux (bool): Remove auxiliary files after compilation
    """

    if not os.path.exists(tex_file):
        print(f"Error: File '{tex_file}' not found.")
        return

    base_name = os.path.splitext(tex_file)[0]

    try:
        for i in range(runs):
            print(f"Compilation pass {i+1}...")
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                print("LaTeX compilation error:")
                print(result.stdout)
                print(result.stderr)
                return

        print(f"\n✅ PDF successfully generated: {base_name}.pdf")

    finally:
        if clean_aux:
            extensions = [".aux", ".log", ".out", ".toc"]
            for ext in extensions:
                aux_file = base_name + ext
                if os.path.exists(aux_file):
                    os.remove(aux_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compile_latex.py <file.tex>")
    else:
        tex_file = sys.argv[1]
        compile_latex(tex_file)