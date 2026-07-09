import zipfile
from pathlib import Path
import make_wheels as mw

def test_build_wheel(tmp_path):
    whl = mw.build_wheel(Path('downloads/j9.7.1_linux.tar.gz'), 'manylinux_2_34_x86_64', tmp_path)
    assert whl.name == f'jlanguage-{mw.JVER}-py3-none-manylinux_2_34_x86_64.whl'
    with zipfile.ZipFile(whl) as z:
        names = z.namelist()
        di = f'jlanguage-{mw.JVER}.dist-info'
        for n in ['jlang/__init__.py','jlang/__main__.py','jlang/bin/jconsole','jlang/bin/libj.so',
                  'jlang/bin/profile.ijs','jlang/system/util/boot.ijs',f'{di}/METADATA',f'{di}/WHEEL',
                  f'{di}/entry_points.txt',f'{di}/RECORD']: assert n in names, n
        assert not any(n.startswith('j9.7/') for n in names)
        jc = z.getinfo('jlang/bin/jconsole')
        assert jc.external_attr>>16 & 0o111, 'jconsole must be executable'
        assert jc.create_system==3
        assert f'Tag: py3-none-manylinux_2_34_x86_64' in z.read(f'{di}/WHEEL').decode()
        md = z.read(f'{di}/METADATA').decode()
        assert 'Name: jlanguage' in md and f'Version: {mw.JVER}' in md
        assert 'jconsole = jlang:main' in z.read(f'{di}/entry_points.txt').decode()
        init = z.read('jlang/__init__.py').decode()
        assert mw.JVER in init and 'def main' in init
        record = z.read(f'{di}/RECORD').decode()
        assert 'jlang/bin/jconsole,sha256=' in record
