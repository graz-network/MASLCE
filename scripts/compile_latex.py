from pathlib import Path
import subprocess
import shutil
import sys


def compile_tex_file(tex_file: Path) -> bool:
    tex_file = tex_file.resolve()
    workdir = tex_file.parent

    # 1) Compiler recommandé si disponible
    latexmk = shutil.which("latexmk")
    if latexmk:
        cmd = [
            latexmk,
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_file.name,
        ]
    else:
        # 2) Fallback vers pdflatex (deux passes)
        pdflatex = shutil.which("pdflatex")
        if not pdflatex:
            print(f"[ERREUR] Aucun compilateur LaTeX trouvé pour: {tex_file}")
            print("         Installe 'latexmk' ou 'pdflatex'.")
            return False

        try:
            for i in range(2):
                result = subprocess.run(
                    [
                        pdflatex,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        tex_file.name,
                    ],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
            print(f"[OK] {tex_file}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ECHEC] {tex_file}")
            print(e.stdout)
            print(e.stderr)
            return False

    # Cas latexmk
    try:
        result = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"[OK] {tex_file}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[ECHEC] {tex_file}")
        print(e.stdout)
        print(e.stderr)
        return False


def compile_all_tex_files(root_dir: str) -> None:
    root = Path(root_dir).resolve()

    if not root.exists() or not root.is_dir():
        print(f"[ERREUR] Répertoire invalide: {root}")
        sys.exit(1)

    tex_files = sorted(root.rglob("*.tex"))

    if not tex_files:
        print(f"Aucun fichier .tex trouvé dans {root}")
        return

    print(f"{len(tex_files)} fichier(s) .tex trouvé(s) dans {root}\n")

    success = 0
    failed = 0

    for tex_file in tex_files:
        if compile_tex_file(tex_file):
            success += 1
        else:
            failed += 1

    print("\n--- Résumé ---")
    print(f"Succès : {success}")
    print(f"Échecs : {failed}")


if __name__ == "__main__":
    # Usage:
    # python compile_all_tex.py /chemin/vers/le/repertoire
    if len(sys.argv) != 2:
        print("Usage: python compile_all_tex.py ../reports")
        sys.exit(1)

    compile_all_tex_files(sys.argv[1])