import pathlib
import sys
__version__ = '0.1'

sys.path.append('..\\')
DATADIR = \
    pathlib.Path(__file__).parent.resolve() / pathlib.Path('data')
TESTDIR = \
    pathlib.Path(__file__).parent.parent.resolve() / pathlib.Path('tests')

from freefield.devices import Devices
