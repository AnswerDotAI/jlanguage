# jlanguage

The [J programming language](https://www.jsoftware.com), installable with pip. This is an unofficial packaging, not affiliated with Jsoftware: J's home page is [jsoftware.com](https://www.jsoftware.com) and its official source is [jsoftware/jsource](https://github.com/jsoftware/jsource). These wheels repackage the official J binary releases, unmodified, so that `pip install jlanguage` gives you a working J on Linux (x86_64, aarch64), macOS (Intel and Apple Silicon), and Windows (amd64, arm64).

## Usage

```
pip install jlanguage
jconsole
```

That starts the standard J console REPL:

```
   +/ % # 1 2 3 4
0.25
```

`python -m jlang` does the same thing, useful when scripts aren't on your PATH. From Python, `jlang.path()` returns the install directory (containing `bin/`, `system/`, `addons/`, `tools/`) and `jlang.jconsole_path()` the full path to the executable.

## Versioning

The package version is the J version: `jlanguage 9.7.1` installs J 9.7.1. Packaging-only fixes are released as post versions (`9.7.1.post1`).

## How it's built

`make_wheels.py` downloads each platform's release archive from jsoftware.com, verifies it against the published sha256sums, and writes it into a platform-tagged wheel, following the approach of [ziglang/zig-pypi](https://github.com/ziglang/zig-pypi). Nothing is compiled and the binaries are byte-identical to the official ones.

## License

J is © Jsoftware Inc. and distributed under the GPLv3 (see [jsoftware/jsource](https://github.com/jsoftware/jsource)). This package redistributes the official binaries unmodified.

## Releasing a new version

When Jsoftware publishes a new J release:

1. Update `JVER` in `make_wheels.py`. The download URL is derived from it, so nothing else normally changes; do check the archive names against [the install dir](https://www.jsoftware.com/download/) since the suffixes have changed between releases (9.6.3 used `linux64`, 9.7.1 uses `linux`).
2. Run `python make_wheels.py`. It downloads each platform archive (cached in `downloads/`), verifies it against the published sha256sums, and writes the wheels to `dist/`.
3. Run `pytest -q`, then `twine upload dist/*.whl`.

For a packaging-only fix to an already-released J version, append `.postN` to the version.
