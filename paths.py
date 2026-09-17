"""Shared paths. Everything resolves relative to the repository root, so the
scripts work from anywhere and nothing depends on an absolute location.

Also the one place the console encoding is dealt with. Half the tools print
Japanese, and a Windows console is cp1252 by default, so without this
`check_script.py` and `battle_names.py` die on their first kana - not on
anything to do with the ROM. Python 3.15 makes UTF-8 the default and this
becomes a no-op; until then it is needed.
"""
import os, sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass                       # redirected to something that cannot be set

ROOT = os.path.dirname(os.path.abspath(__file__))
ROM_IN = os.path.join(ROOT, 'rom', 'Wondrous_Magic__Japan_.sfc')
ROM_OUT = os.path.join(ROOT, 'rom', 'Wondrous_Magic_EN.sfc')
DATA = os.path.join(ROOT, 'data')
ASSETS = os.path.join(ROOT, 'assets')

for d in ('tools', 'build'):
    p = os.path.join(ROOT, d)
    if p not in sys.path:
        sys.path.insert(0, p)


def rom():
    if not os.path.exists(ROM_IN):
        raise SystemExit('put the Japanese ROM at %s' % ROM_IN)
    return bytearray(open(ROM_IN, 'rb').read())
