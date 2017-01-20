#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Inital version by Mathis Börner
import numpy as np
import pandas as pd
from fnmatch import fnmatch


def get_nan_ratio(df, white_list, weight=None, rel=True):
    # init nan_count with zeros
    nan_count = pd.Series(0., index=white_list)
    # check if weight is given and in proper shape
    if not weight is None:
        if len(weight) > 1:
            weight = weight.flatten()
        denominator = np.sum(weight)
    else:
        weight = 1.
        denominator = len(df)

    # calculate nan count/ratio for each attribute, taking weight into account
    for o in white_list:
        nan_array = np.array(df[o].isnull(), dtype=float)
        nan_count[o] = np.sum(nan_array * weight)
        if rel:
            nan_count[o] /= denominator
    return nan_count


def get_nan_ratio_total(dfs, white_list, weight=None):
    sum_ws = [np.sum(df[weight]) for df in dfs]
    nan_ratios = [get_nan_ratio(df, white_list, weight) for df in dfs]
    nan_ratios = np.array(nan_ratios)
    nan_vals = np.zeros(len(white_list), dtype=float)
    for i in range(len(dfs)):
        nan_vals += nan_ratios[i, :] * sum_ws[i]
    nan_vals /= np.sum(sum_ws)
    return pd.Series(nan_vals, index=white_list)


def get_dups(df, white_list, threshold=0.5):
    blacklist = [o for o in list(df.columns) if o not in white_list]
    df_obs = df.drop(blacklist,axis=1)
    corr_mat = df_obs.corr('pearson')
    return process_correlation_matrix(corr_mat, threshold=threshold)


def process_correlation_matrix(corr_mat, threshold=1.0):
    dups = []
    counter = 0
    while True:
        col = corr_mat.columns[counter]
        if not np.isfinite(corr_mat[col][col]):
            corr_mat.drop(col,axis=0,inplace=True)
            corr_mat.drop(col,axis=1,inplace=True)
            dups.append(col)
        else:
            similar_cols = abs(corr_mat[col]) >= threshold
            indices = list(similar_cols[similar_cols].index)
            indices.remove(col)
            if len(indices) != 0:
                dups.extend(indices)
                corr_mat.drop(indices,axis=0,inplace=True)
                corr_mat.drop(indices,axis=1,inplace=True)
            counter += 1
        if counter >= len(corr_mat.columns):
            break
    return dups


def get_dups_n_thresholds(df, white_list, thresholds):
    blacklist = [o for o in list(df.columns) if o not in white_list]
    df_obs = df.drop(blacklist,axis=1)
    corr_mat = df_obs.corr('pearson')
    thresholds = np.sort(thresholds)
    n_thresholds = len(thresholds)
    dups = []
    for i, t in enumerate(thresholds[::-1]):
        dups.append(process_correlation_matrix(corr_mat, t))
    n_dups_sum = np.cumsum([len(d) for d in dups])
    return dups[::-1], n_dups_sum[::-1], thresholds


def generate_black_list_from_dups(dups, thresholds, sel_threshold):
    index = np.argwhere(thresholds >= sel_threshold)[0]
    blacklist = []
    for i in range(index, len(dups)):
        blacklist.extend(dups[i])
    return blacklist


def get_constants(df, white_list):
    blacklist = [o for o in list(df.columns) if o not in white_list]
    df_obs = df.drop(blacklist,axis=1)
    std = df_obs.std(skipna=True)
    return list(std[std == 0].index)


def get_atts_pattern(white_list, patterns):
    if isinstance(patterns, str):
        patterns = [patterns]
    matches = []
    for pattern in patterns:
        for i in white_list:
            if fnmatch(i, pattern):
                matches.append(i)
    return matches
