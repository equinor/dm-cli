#!/usr/bin/env python

import sys
import os

dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src')

if os.environ.get('PYTHONPATH') is None:
    os.environ['PYTHONPATH'] = dir
else:
    os.environ['PYTHONPATH'] = os.pathsep.join([
        dir,
        os.environ.get('PYTHONPATH'),
    ])

os.execl(sys.executable, sys.executable, '-m', 'dm', *sys.argv[1:])