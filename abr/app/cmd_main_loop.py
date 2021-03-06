from collections import Counter
import enaml
from enaml.qt.qt_application import QtApplication

import argparse
import os.path

from abr.parsers import Parser

from . import add_default_arguments, parse_args


with enaml.imports():
    from abr.main_window import SerialWindow
    from abr.presenter import SerialWaveformPresenter


def main():
    parser = argparse.ArgumentParser("abr_loop")
    add_default_arguments(parser)
    parser.add_argument('dirnames', nargs='*')
    parser.add_argument('--list', action='store_true')
    options = parse_args(parser)
    parser = options['parser']

    unprocessed = []
    for dirname in options['dirnames']:
        unprocessed.extend(parser.find_unprocessed(dirname))

    if options['list']:
        counts = Counter(f for f, _ in unprocessed)
        for filename, n in counts.items():
            filename = os.path.basename(filename)
            print(f'{filename} ({n})')

    else:
        app = QtApplication()
        presenter = SerialWaveformPresenter(parser=parser,
                                            unprocessed=unprocessed)
        view = SerialWindow(presenter=presenter)
        view.show()
        app.start()
        app.stop()
