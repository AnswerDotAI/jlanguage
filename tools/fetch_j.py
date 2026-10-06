#!/usr/bin/env python3
"Download the official J release for this platform from jsoftware.com, verify it, and unpack it into `python/jlang/j/`."
import hashlib, platform, shutil, sys, tarfile, tomllib, urllib.request, zipfile
from pathlib import Path
from functools import cache

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT/'python'/'jlang'/'j'
# The package version is J's version followed by jlanguage's own release number.
JVER = '.'.join(tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'].split('.')[:3])
BASEURL = f"https://www.jsoftware.com/download/j{JVER.rsplit('.',1)[0]}/install/"
PLATFORMS = {  # Archive suffix -> wheel tag, (sys.platform, machine) pairs
    'linux.tar.gz': ('manylinux_2_34_x86_64', [('linux', 'x86_64')]),
    'raspi.tar.gz': ('manylinux_2_38_aarch64', [('linux', 'aarch64')]),
    'mac.zip': ('macosx_10_9_universal2', [('darwin', 'arm64'), ('darwin', 'x86_64')]),
    'win.zip': ('win_amd64', [('win32', 'AMD64')]),
    'winarm.zip': ('win_arm64', [('win32', 'ARM64')])}
ARCHIVES = {system:suffix for suffix,(_,systems) in PLATFORMS.items() for system in systems}

def archive_name(plat=sys.platform, machine=platform.machine()):
    "The jsoftware archive for `plat` and `machine`"
    return f'j{JVER}_{ARCHIVES[plat, machine]}'

@cache
def checksums():
    return dict(reversed(line.split()) for line in urllib.request.urlopen(BASEURL+'sha256sums').read().decode().strip().splitlines())

def fetch(fname, dl=ROOT/'downloads'):
    "Download `fname` into `dl` if not cached, and verify its sha256"
    dl.mkdir(exist_ok=True)
    p = dl/fname
    if not p.exists(): urllib.request.urlretrieve(BASEURL+fname, p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==checksums()[fname], f'sha256 mismatch for {fname}'
    return p

def archive_files(path):
    "Yield (relpath, mode, data) for each file, with the archive's root directory, such as `j9.7/`, stripped"
    if path.name.endswith('.tar.gz'):
        with tarfile.open(path) as tar:
            for m in tar:
                if m.isfile(): yield m.name.split('/',1)[1], m.mode&0o777, tar.extractfile(m).read()
    else:
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                if not i.is_dir(): yield i.filename.split('/',1)[1], (i.external_attr>>16)&0o777 or 0o644, z.read(i)

def unpack(archive, dest=DEST):
    "Replace `dest` with the files of `archive`, keeping their permissions"
    shutil.rmtree(dest, ignore_errors=True)
    for rel,mode,data in archive_files(archive):
        p = dest/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        p.chmod(mode)
    return dest

if __name__=='__main__': print(unpack(fetch(archive_name())))
