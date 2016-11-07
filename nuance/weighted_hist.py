# coding: utf-8

from functools import reduce
from hdfchain import HDFChain
import numpy as np


def getBinBorders(all_data, BINS):
    '''
        Returns bin sequence, for given dataset, and number of bins,
        as well as a boolean value stating whether sequence is on log scale
    '''
    BIN_MIN = np.nanmin(all_data)
    BIN_MAX = np.nanmax(all_data)
    print("Min: {} Max: {}".format(BIN_MIN, BIN_MAX))
    # ToDo negativ min/max -> linspace
    if (BIN_MAX - BIN_MIN) > 100 and BIN_MAX > 0 and BIN_MIN > 0:
        # log scale
        if BIN_MIN <= 0:
            BIN_MIN = 0
        else:
            BIN_MIN = np.log10(BIN_MIN)
        BIN_MAX = np.log10(BIN_MAX)

        return np.logspace(BIN_MIN, BIN_MAX, BINS+1), True
    elif (BIN_MAX - BIN_MIN) == 0 or np.isnan(BIN_MAX - BIN_MIN):
        return None, False
    else:
        return np.linspace(BIN_MIN, BIN_MAX, BINS+1), False


def getXvalues(bin_borders):
    '''
        Returns bin centers and halfwidhts for given bin sequence
    '''
    left, right = bin_borders[:-1], bin_borders[1:]
    points = {'center': left + right,
              'halfwidth': right - left}
    points.update((key, value * 0.5) for key, value in points.items())

    return points['center'], points['halfwidth']


def getYvalues(values, nfiles, BINS, bin_borders, lifetime=None, weights=None):
    '''
        Returns y values for weighted histograms, as well as its errors
        Errors are sq roots of summed up weights divided by nfiles
        
    '''
    binIndex = np.digitize(values, bin_borders)
    if weights is None:
        y, _ = np.histogram(values, bins=bin_borders)
        errors = np.sqrt(y)
    else:
        y = np.zeros(BINS)
        errors = np.zeros(BINS)
        for i, v in enumerate(binIndex):
            if v > 0 and v <= BINS and i < len(weights):
                y[v-1] += (weights[i] / nfiles)
                errors[v-1] += (weights[i] / nfiles) ** 2

        errors = np.sqrt(errors)
        if lifetime:
            y *= lifetime
            errors *= lifetime

    return y, errors


def loadData(paths):
    '''
        paths: paths in basepath for data sets to load
        return: dictionary with loaded data sets, list of all shared attributes
    '''
    data = {}
    all_attributes = []
    for dataset, path in paths.items():
        data[dataset] = HDFChain(path)
        all_attributes.append(data[dataset]._tables.keys())

    attributes = reduce(set.intersection, map(set, all_attributes))

    return data, attributes
