"""Shared paths. Everything resolves relative to the repository root, so the
scripts work from anywhere and nothing depends on an absolute location."""
import os, sys

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
