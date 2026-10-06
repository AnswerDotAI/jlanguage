"""The J programming language, with J sessions, IPython magics and a Jupyter kernel for Python.

Modules:

- `jlang.core`: Run the J language from Python and Jupyter through libj: sessions, magics and a Jupyter kernel."""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
import os, subprocess, sys

__version__ = version('jlanguage')


def path():
    "The bundled J installation: the directory holding `bin`, `system`, `addons` and `tools`."
    return Path(files('jlang'))/'j'


def jconsole_path():
    "The full path of the bundled J console."
    return path()/'bin'/('jconsole.exe' if os.name=='nt' else 'jconsole')


def main():
    "Run J's console, passing on the command line's arguments."
    argv = [str(jconsole_path()), *sys.argv[1:]]
    if os.name=='posix': os.execv(argv[0], argv)
    sys.exit(subprocess.call(argv))
