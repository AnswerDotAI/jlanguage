from email import message_from_bytes
import fetch_j, make_wheels
from build import ProjectBuilder
from pathlib import Path
from wheel.wheelfile import WheelFile


def test_bundled_wheels(tmp_path):
    wrapper = Path(ProjectBuilder(fetch_j.ROOT).build('wheel', str(tmp_path)))
    for suffix,(plat,_) in fetch_j.PLATFORMS.items():
        archive = fetch_j.fetch(f'j{fetch_j.JVER}_{suffix}')
        wheel = make_wheels.build_wheel(wrapper, archive, plat, tmp_path)
        with WheelFile(wheel) as whl:
            names = whl.namelist()
            assert 'jlang/_engine.py' in names and 'jlang/core.py' in names
            assert not any(n.startswith('jlang/_core.') for n in names)
            metadata = message_from_bytes(whl.read(next(n for n in names if n.endswith('.dist-info/METADATA'))))
            deps = metadata.get_all('Requires-Dist')
            assert 'fastcore' in deps and 'kernmini>=0.1.19' in deps
            assert metadata['Requires-Python'] == '>=3.11'
            assert not {'python', 'kernel'}.intersection(metadata.get_all('Provides-Extra'))
            assert f'Tag: py3-none-{plat}' in whl.read(next(n for n in names if n.endswith('.dist-info/WHEEL'))).decode()
            assert b'Root-Is-Purelib: false' in whl.read(next(n for n in names if n.endswith('.dist-info/WHEEL')))
            for rel,mode,data in fetch_j.archive_files(archive):
                if rel.startswith('bin/') and ('jconsole' in rel or rel.endswith(('.dll', '.so', '.dylib', 'profile.ijs'))):
                    assert whl.read(f'jlang/j/{rel}') == data
                    assert (whl.getinfo(f'jlang/j/{rel}').external_attr>>16)&0o777 == mode
            spec = next(n for n in names if n.endswith('/share/jupyter/kernels/j/kernel.json'))
            assert b'"interrupt_mode": "message"' in whl.read(spec)
