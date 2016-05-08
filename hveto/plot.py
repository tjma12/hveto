# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
#
# This file is part of the hveto python package.
#
# hveto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hveto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hveto.  If not, see <http://www.gnu.org/licenses/>.

"""Plotting routines for hveto
"""

from __future__ import division

from math import (log10, floor)

from matplotlib.colors import LogNorm

from gwpy.plotter import (rcParams, HistogramPlot, EventTablePlot,
                          TimeSeriesPlot, Plot)
from gwpy.plotter.table import get_column_string

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda'

rcParams.update({
    'figure.subplot.bottom': 0.17,
    'figure.subplot.left': 0.1,
    'figure.subplot.right': 0.9,
    'figure.subplot.top': 0.90,
    'axes.labelsize': 24,
    'axes.labelpad': 2,
    'grid.color': 'gray',
})


def before_after_histogram(
        outfile, x, y, label1='Before', label2='After',
        bins=100, histtype='stepfilled', range=None, figsize=[9, 6], **kwargs):
    """Plot a histogram of SNR for two event distributions
    """
    # format axis arguments
    axargs = {
        'xscale': 'log',
        'xlabel': 'Loudness',
        'yscale': 'log',
        'ylabel': 'Number of events',
    }
    axargs.update(kwargs)
    # create figure
    plot = HistogramPlot(figsize=figsize)
    ax = plot.gca()
    # make histogram
    if range is None:
        range = ax.common_limits((x, y))
    axargs.setdefault('xlim', range)
    histargs = {
        'range': range,
        'histtype': histtype,
        'bins': bins,
        'linewidth': 2,
        'logbins': axargs['xscale'] == 'log',
        'alpha': .8,
    }
    ax.hist(x, label=label1, facecolor='red', edgecolor='darkred',
            **histargs)
    ax.hist(y, label=label2, facecolor='dodgerblue', edgecolor='blue',
            **histargs)
    # add legend
    ax.legend(loc='upper right')
    # format axes
    axargs.setdefault('ylim', (.5, ax.yaxis.get_data_interval()[1] * 1.05))
    _finalize_plot(plot, ax, outfile, **axargs)


def veto_scatter(
        outfile, a, b, label1='All', label2='Vetoed', x='time', y='snr',
        color=None, clim=None, clabel=None, cmap=None, clog=True,
        figsize=[9, 6],**kwargs):
    """Plot an x-y scatter of all/vetoed events
    """
    # format axis arguments
    axargs = {
        'yscale': 'log',
        'ylabel': 'Loudness',
    }
    if x != 'time':
        axargs['xscale'] = 'log'
    axargs.update(kwargs)
    # create figure
    plot = EventTablePlot(base=x=='time' and TimeSeriesPlot or Plot,
                          figsize=figsize)
    ax = plot.gca()
    # add data
    scatterargs = {'s': 40}
    if color is None:
        ax.scatter(a[x], a[y], color='black', marker='o', label=label1, s=40)
    else:
        colorargs = {'edgecolor': 'none'}
        if clim:
            colorargs['vmin'] = clim[0]
            colorargs['vmax'] = clim[1]
            if clog:
                colorargs['norm'] = LogNorm(vmin=clim[0], vmax=clim[1])
        a = a.copy()
        a.sort(order=color)
        m = ax.scatter(a[x], a[y], c=a[color], label=label1, **colorargs)
        # add colorbar
        plot.add_colorbar(mappable=m, ax=ax, cmap=cmap, label=clabel)
        # unsort them
        a.sort(order='time')
    if isinstance(b, list):
        colors = list(rcParams['axes.prop_cycle'])
    else:
        b = [b]
        label2 = [label2]
        colors = [{'color': 'red'}]
    for i, data in enumerate(b):
        # setting the color here looks complicated, but is just a fancy
        # way of looping through the color cycle when scattering, but using
        # red if we only have one other data set
        ax.scatter(data[x], data[y], marker='+', linewidth=1.5,
                   label=label2[i], s=40, **colors[i % len(colors)])
    # add legend
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc='upper right')
    # finalize
    for axis in ['x', 'y']:
        lim = list(getattr(ax, '%saxis' % axis).get_data_interval())
        lim[0] = axargs.get('%sbound' % axis, lim[0])
        axargs.setdefault('%slim' % axis, (lim[0] * 0.95, lim[1] * 1.05))
    _finalize_plot(plot, ax, outfile, **axargs)


def _finalize_plot(plot, ax, outfile, bbox_inches=None, **axargs):
    xlim = axargs.pop('xlim', None)
    ylim = axargs.pop('ylim', None)
    # set title and subtitle
    subtitle = axargs.pop('subtitle', None)
    # format axes
    for key in axargs:
        getattr(ax, 'set_%s' % key)(axargs[key])
    if subtitle:
        pos = list(ax.title.get_position())
        pos[1] += 0.05
        ax.title.set_position(pos)
        ax.text(.5, 1., subtitle, transform=ax.transAxes, va='bottom',
                ha='center')
    # set minor grid for log scale
    if ax.get_xscale() == 'log':
        ax.grid(True, axis='x', which='both')
    if ax.get_yscale() == 'log':
        ax.grid(True, axis='y', which='both')
    # set limits after everything else (matplotlib might undo it)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)
     # add colorbar
    if not plot.colorbars:
        plot.add_colorbar(ax=ax, visible=False)
    # save and close
    plot.save(outfile, bbox_inches=bbox_inches)
    plot.close()


def significance_drop(outfile, old, new, **kwargs):
    """Plot the signifiance drop for each channel
    """
    plot = Plot(figsize=(24, 6))
    ax = plot.gca()
    plot.subplots_adjust(left=.05, right=.95, bottom=.4)

    channels = sorted(old.keys())
    for i, c in enumerate(channels):
        if old[c] > new[c]:
            color = 'dodgerblue'
        else:
            color = 'red'
        ax.plot([i, i], [old[c], new[c]], color=color, linestyle='-',
                marker='o', markersize=10)

    # set xticks to show channel names
    ax.set_xlim(-1, len(channels))
    ax.set_xticks(range(len(channels)))
    ax.set_xticklabels([c.replace('_','\_') for c in channels])
    for i, t in enumerate(ax.get_xticklabels()):
        t.set_rotation(270)
        t.set_verticalalignment('top')
        t.set_horizontalalignment('center')
        t.set_fontsize(8)
        t.set_usetex(False)

    kwargs.setdefault('ylabel', 'Significance')
    _finalize_plot(plot, ax, outfile, **kwargs)


def hveto_roc(outfile, rounds, figsize=[9, 6], **kwargs):
    efficiency = []
    deadtime = []
    for r in rounds:
        try:
            efficiency.append(r.cum_efficiency[0] / r.cum_efficiency[1])
        except ZeroDivisionError:
            efficiency.append(0.)
        try:
            deadtime.append(r.cum_deadtime[0] / r.cum_deadtime[1])
        except ZeroDivisionError:
            deadtime.append(0.)
    plot = Plot(figsize=figsize)
    ax = plot.gca()
    ax.plot(deadtime, efficiency, marker='o', linestyle='-')
    try:
        xbound = 10 ** floor(log10(deadtime[0]))
    except ValueError:
        xbound = 1e-4
    try:
        ybound = 10 ** floor(log10(efficiency[0]))
    except ValueError:
        ybound = 1e-4
    bound = min(xbound, ybound)
    axargs = {
        'xlabel': 'Fractional deadtime',
        'ylabel': 'Fractional efficiency',
        'xscale': 'log',
        'yscale': 'log',
        'xlim': (bound, 1.),
        'ylim': (bound, 1.),
    }
    axargs.update(kwargs)
    _finalize_plot(plot, ax, outfile, **axargs)
