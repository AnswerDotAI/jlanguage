import fetch_j

def test_unpack(tmp_path):
    "J's Linux archive unpacks with its root directory stripped and its console executable"
    dest = fetch_j.unpack(fetch_j.fetch(fetch_j.archive_name('linux', 'x86_64')), tmp_path/'j')
    for f in ['bin/jconsole', 'bin/libj.so', 'bin/profile.ijs', 'system/util/boot.ijs']: assert (dest/f).exists(), f
    assert (dest/'bin/jconsole').stat().st_mode & 0o111, 'jconsole must be executable'
