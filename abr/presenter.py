import numpy as np
import operator
import enaml
import pandas as pd

from atom.api import (Atom, Typed, Dict, List, Bool, Int, Float, Tuple,
                      Property, Value)

from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib import transforms as T

from abr.abrpanel import WaveformPlot
from abr.datatype import ABRSeries, WaveformPoint, Point

# Maximum spacing, in seconds, between positive and negative points of wave.
MAX_PN_DELTA = 0.25

with enaml.imports():
    from abr.main_window import NotificationPopup


def plot_model(axes, model):
    n = len(model.waveforms)
    offset_step = 1/(n+1)
    plots = []

    text_trans = T.blended_transform_factory(axes.figure.transFigure,
                                             axes.transAxes)


    limits = [(w.y.min(), w.y.max()) for w in model.waveforms]
    base_scale = np.mean(np.abs(np.array(limits)))

    bscale_in_box = T.Bbox([[0, -base_scale], [1, base_scale]])
    bscale_out_box = T.Bbox([[0, -1], [1, 1]])
    bscale_in = T.BboxTransformFrom(bscale_in_box)
    bscale_out = T.BboxTransformTo(bscale_out_box)

    tscale_in_box = T.Bbox([[0, -1], [1, 1]])
    tscale_out_box = T.Bbox([[0, 0], [1, offset_step]])
    tscale_in = T.BboxTransformFrom(tscale_in_box)
    tscale_out = T.BboxTransformTo(tscale_out_box)

    boxes = {
        'tscale': tscale_in_box,
        'tnorm': [],
        'norm_limits': limits/base_scale,
    }

    for i, waveform in enumerate(model.waveforms):
        y_min, y_max = waveform.y.min(), waveform.y.max()
        tnorm_in_box = T.Bbox([[0, -1], [1, 1]])
        tnorm_out_box = T.Bbox([[0, -1], [1, 1]])
        tnorm_in = T.BboxTransformFrom(tnorm_in_box)
        tnorm_out = T.BboxTransformTo(tnorm_out_box)
        boxes['tnorm'].append(tnorm_in_box)

        offset = offset_step * i + offset_step * 0.5
        translate = T.Affine2D().translate(0, offset)

        y_trans = bscale_in + bscale_out + \
            tnorm_in + tnorm_out + \
            tscale_in + tscale_out + \
            translate + axes.transAxes
        trans = T.blended_transform_factory(axes.transData, y_trans)

        plot = WaveformPlot(waveform, axes, trans)
        plots.append(plot)

        text_trans = T.blended_transform_factory(axes.transAxes, y_trans)
        axes.text(-0.05, 0, f'{waveform.level}', transform=text_trans)

    axes.set_yticks([])
    axes.grid()
    for spine in ('top', 'left', 'right'):
        axes.spines[spine].set_visible(False)

    return plots, boxes


class WaveformPresenter(Atom):

    figure = Typed(Figure, {})
    axes = Typed(Axes)
    model = Typed(ABRSeries)

    current = Property()

    toggle = Property()
    scale = Property()
    normalized = Property()
    boxes = Dict()


    _current = Int()
    _toggle = Value()
    plots = List()
    N = Bool(False)
    P = Bool(False)

    parser = Value()

    def _default_axes(self):
        axes = self.figure.add_axes([0.1, 0.1, 0.8, 0.8])
        return axes

    def __init__(self, parser):
        self.parser = parser

    def load(self, model):
        self._current = 0
        self.axes.clear()
        self.axes.set_xlabel('Time (msec)')
        self.model = model
        self.plots, self.boxes = plot_model(self.axes, self.model)
        self.normalized = False
        self.N = False
        self.P = False

        # Set current before toggle. Ordering is important.
        self.current = len(self.model.waveforms)-1
        self.toggle = None
        self.update()

    def save(self):
        if  np.isnan(self.model.threshold):
            raise ValueError('Threshold not set')
        if not self.P or not self.N:
            raise ValueError('Waves not identified')
        # msg = registry.save(self.model, self.options)
        # print(msg)
        self.parser.save(self.model)
        NotificationPopup().show()

    def update(self):
        for p in self.plots:
            p.update()
        if self.axes.figure.canvas is not None:
            self.axes.figure.canvas.draw()

    def _get_current(self):
        return self._current

    def _set_current(self, value):
        if not (0 <= value < len(self.model.waveforms)):
            return
        if value == self.current:
            return
        self.plots[self.current].current = False
        self.plots[value].current = True
        self._current = value
        self.update()

    def _get_scale(self):
        return self.boxes['tscale'].ymax

    def _set_scale(self, value):
        if value < 0:
            return
        box = np.array([[0, -value], [1, value]])
        self.boxes['tscale'].set_points(box)
        self.update()

    def _get_normalized(self):
        box = self.boxes['tnorm'][0]
        return not ((box.ymin == -1) and (box.ymax == 1))

    def _set_normalized(self, value):
        if value:
            zipped = zip(self.boxes['tnorm'], self.boxes['norm_limits'])
            for box, (lb, ub) in zipped:
                points = np.array([[0, lb], [1, ub]])
                box.set_points(points)
        else:
            for box in self.boxes['tnorm']:
                points = np.array([[0, -1], [1, 1]])
                box.set_points(points)
        label = 'normalized' if value else 'raw'
        self.axes.set_title(label)
        self.update()

    def set_suprathreshold(self):
        self.model.threshold = -np.inf
        self.update()

    def set_subthreshold(self):
        self.model.threshold = np.inf
        if not self.P:
            self.guess_p()
        if not self.N:
            self.guess_n()
        self.save()
        self.update()

    def set_threshold(self):
        self.model.threshold = self.get_current_waveform().level
        self.update()

    def _get_toggle(self):
        return self._toggle

    def _set_toggle(self, value):
        if value == self._toggle:
            return
        for plot in self.plots:
            point = plot.points.get(self.toggle)
            if point is not None:
                point.current = False
        self._toggle = value
        for plot in self.plots:
            point = plot.points.get(value)
            if point is not None:
                point.current = True
        self.update()

    def guess(self):
        if not self.P:
            self.model.guess_p()
            ptype = Point.PEAK
            self.P = True
        elif not self.N:
            self.model.guess_n()
            ptype = Point.VALLEY
            self.N = True
        else:
            return
        self.update()
        self.current = len(self.model.waveforms)-1
        self.toggle = 1, ptype
        self.update()

    def update_point(self):
        level = self.model.waveforms[self.current].level
        self.model.update_guess(level, self.toggle)
        self.update()

    def move_selected_point(self, step):
        point = self.get_current_point()
        point.move(step)
        self.update()

    def get_current_waveform(self):
        return self.model.waveforms[self.current]

    def get_current_point(self):
        return self.get_current_waveform().points[self.toggle]


class SerialWaveformPresenter(WaveformPresenter):

    unprocessed = List()
    current_model = Int(-1)

    def __init__(self, parser, unprocessed):
        super().__init__(parser)
        self.unprocessed = unprocessed
        self.load_next()

    def load_prior(self):
        if self.current_model < 0:
            return
        self.current_model -= 1
        filename, frequency = self.unprocessed[self.current_model]
        model = self.parser.load(filename, frequencies=[frequency])[0]
        self.load(model)

    def load_next(self):
        if self.current_model >= len(self.unprocessed):
            return
        self.current_model += 1
        filename, frequency = self.unprocessed[self.current_model]
        model = self.parser.load(filename, frequencies=[frequency])[0]
        self.load(model)

    def save(self):
        super().save()
        self.load_next()
