#!/usr/bin/env python3
"Repackage official J language binaries from jsoftware.com into platform wheels (ziglang/zig-pypi approach)."
import hashlib, tarfile, urllib.request, zipfile
from pathlib import Path
from zipfile import ZipInfo, ZIP_DEFLATED
from wheel.wheelfile import WheelFile

DIST = 'jlanguage'  # PyPI distribution name; the import package stays `jlang`
JVER = '9.7.1'
BASEURL = f"https://www.jsoftware.com/download/j{JVER.rsplit('.',1)[0]}/install/"
PLATFORMS = {  # jsoftware archive suffix -> wheel platform tag
    'linux.tar.gz': 'manylinux_2_34_x86_64',
    'raspi.tar.gz': 'manylinux_2_38_aarch64',
    'mac.zip':      'macosx_10_9_universal2',
    'win.zip':      'win_amd64',
    'winarm.zip':   'win_arm64'}

INIT = f'''import os, sys, subprocess
__version__ = {JVER!r}

def path():
    "Directory containing the J installation (bin/, system/, addons/, tools/)"
    return os.path.dirname(os.path.abspath(__file__))

def jconsole_path():
    "Full path to the bundled jconsole executable"
    return os.path.join(path(), 'bin', 'jconsole.exe' if os.name=='nt' else 'jconsole')

def main():
    "Run jconsole, passing along any command line args"
    argv = [jconsole_path(), *sys.argv[1:]]
    if os.name=='posix': os.execv(argv[0], argv)
    sys.exit(subprocess.call(argv))
'''

MAIN = 'from jlang import main\nmain()\n'
EPS = '[console_scripts]\njconsole = jlang:main\n'

def metadata():
    readme = Path('README.md').read_text() if Path('README.md').exists() else 'The J programming language.'
    return f'''Metadata-Version: 2.1
Name: {DIST}
Version: {JVER}
Summary: The J programming language, repackaged from official jsoftware.com binaries
Home-page: https://github.com/AnswerDotAI/jlanguage
Project-URL: Documentation, https://code.jsoftware.com/wiki
Project-URL: Source, https://github.com/AnswerDotAI/jlanguage
Project-URL: J home page, https://www.jsoftware.com
Author: Jsoftware Inc.
License: GPL-3.0-or-later
Classifier: License :: OSI Approved :: GNU General Public License v3 (GPLv3)
Classifier: Programming Language :: Other
Description-Content-Type: text/markdown

{readme}'''

def wheel_meta(plat):
    return f'''Wheel-Version: 1.0
Generator: {DIST} make_wheels.py
Root-Is-Purelib: false
Tag: py3-none-{plat}
'''

def zinfo(arcname, mode=0o644):
    i = ZipInfo(arcname, (1980,1,1,0,0,0))
    i.external_attr = (0o100000|mode)<<16
    i.create_system = 3
    i.compress_type = ZIP_DEFLATED
    return i

def archive_files(path):
    "Yield (relpath, mode, data) for each file, with the j9.7/ root dir stripped"
    if path.name.endswith('.tar.gz'):
        with tarfile.open(path) as tar:
            for m in tar:
                if m.isfile(): yield m.name.split('/',1)[1], m.mode&0o777, tar.extractfile(m).read()
    else:
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                if not i.is_dir(): yield i.filename.split('/',1)[1], (i.external_attr>>16)&0o777 or 0o644, z.read(i)

def build_wheel(
    archive, # Path to a downloaded jsoftware release archive
    plat,    # Wheel platform tag, e.g. 'manylinux_2_34_x86_64'
    out_dir, # Directory to write the wheel into
):
    "Repackage `archive` as a wheel tagged `plat`; returns the wheel path"
    di = f'{DIST}-{JVER}.dist-info'
    out = Path(out_dir)/f'{DIST}-{JVER}-py3-none-{plat}.whl'
    with WheelFile(out, 'w') as whl:
        for rel,mode,data in archive_files(archive): whl.writestr(zinfo(f'jlang/{rel}', mode), data)
        whl.writestr(zinfo('jlang/__init__.py'), INIT)
        whl.writestr(zinfo('jlang/__main__.py'), MAIN)
        whl.writestr(zinfo(f'{di}/entry_points.txt'), EPS)
        whl.writestr(zinfo(f'{di}/WHEEL'), wheel_meta(plat))
        whl.writestr(zinfo(f'{di}/METADATA'), metadata())
    return out

def fetch(fname, dl=Path('downloads')):
    "Download `fname` into `dl` if not cached, and verify its sha256"
    dl.mkdir(exist_ok=True)
    sums = dict(reversed(l.split()) for l in urllib.request.urlopen(BASEURL+'sha256sums').read().decode().strip().splitlines())
    p = dl/fname
    if not p.exists(): urllib.request.urlretrieve(BASEURL+fname, p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==sums[fname], f'sha256 mismatch for {fname}'
    return p

def main():
    out = Path('dist')
    out.mkdir(exist_ok=True)
    for suffix,plat in PLATFORMS.items():
        whl = build_wheel(fetch(f'j{JVER}_{suffix}'), plat, out)
        print(whl, whl.stat().st_size)

if __name__=='__main__': main()
