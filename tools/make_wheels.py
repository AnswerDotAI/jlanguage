#!/usr/bin/env python3
"Package the Python wrapper and official J releases into platform wheels without compiling."
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipInfo, ZipFile
from build import ProjectBuilder
from wheel.wheelfile import WheelFile
from fetch_j import ROOT, JVER, PLATFORMS, archive_files, fetch


def build_wheel(wrapper, archive, plat, out_dir):
    "Add `archive` to the Python `wrapper` wheel and tag it for `plat`."
    out = Path(out_dir)/wrapper.name.replace('py3-none-any', f'py3-none-{plat}')
    with ZipFile(wrapper) as src, WheelFile(out, 'w') as whl:
        for info in src.infolist():
            if info.filename.endswith('.dist-info/RECORD'): continue
            data = src.read(info)
            if info.filename.endswith('.dist-info/WHEEL'):
                data = data.replace(b'Root-Is-Purelib: true', b'Root-Is-Purelib: false').replace(b'Tag: py3-none-any', f'Tag: py3-none-{plat}'.encode())
            whl.writestr(info, data)
        for rel,mode,data in archive_files(archive):
            info = ZipInfo(f'jlang/j/{rel}')
            info.external_attr = (0o100000|mode)<<16
            info.create_system,info.compress_type = 3,ZIP_DEFLATED
            whl.writestr(info, data)
    return out


def main():
    out = ROOT/'dist'
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wrapper = Path(ProjectBuilder(ROOT).build('wheel', tmp))
        for suffix,(plat,_) in PLATFORMS.items(): print(build_wheel(wrapper, fetch(f'j{JVER}_{suffix}'), plat, out))


if __name__=='__main__': main()
