#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Inital version by Mathis Börner
import pickle

import numpy as np
import pandas as pd
from fnmatch import fnmatch



def get_nan_ratio(df, white_list, weight=None, rel=True):
    nan_ratio = pd.Series(0., index=white_list)
    if weight is not None:
        w_array = np.array(df[weight])
        sum_w = np.sum(w_array)
        for o in white_list:
            nan_array = np.array(df[o].isnull(), dtype=float)
            if rel:
                nan_ratio[o] = np.sum(nan_array * w_array) / sum_w
    else:
        n_row = len(df)
        for o in white_list:
            nan_array = np.array(df[o].isnull(), dtype=float)
            if rel:
                nan_ratio[o] = nan_array / float(n_row)
    return nan_ratio


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


if __name__ == '__main__':
    from mtools.utils.i3hdf_to_df import HDFcontainer
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--dataset",
                      dest="dataset",
                      type="str",
                      default='11058')

    (opts, args) = parser.parse_args()

    with open('data_only_att.dat') as f:
        df_obs = cPickle.load(f)


    dataset = opts.dataset
    if dataset == '11058':
        hdf_container = HDFcontainer(file_list=['11058.hdf5'],
                                         exists_col='exists')
        out_file = 'result_11058.dat'
        w = 'CorsikaWeights.GaisserH3aWeight'
    elif dataset == '11057':
        hdf_container = HDFcontainer(file_list=['11057.hdf5'],
                                         exists_col='exists')
        out_file = 'result_11057.dat'
        w = 'CorsikaWeights.GaisserH3aWeight'
    elif dataset == '11374':
        hdf_container = HDFcontainer(
            file_list=['Level4_IC86.2012_nugen_numu.011374.0_100_100Files.clsim-base-4.0.3.0.99_eff.hd5', 'Level4_IC86.2012_nugen_numu.011374.101_200_100Files.clsim-base-4.0.3.0.99_eff.hd5'], exists_col='exists')
        out_file = 'result_11374.dat'
        w = 'NeutrinoWeights.honda2006_gaisserH3a_elbert_v2_numu_conv_nuflux'

    elif dataset == 'all':

        w = 'CorsikaWeights.GaisserH3aWeight'
        container = HDFcontainer(file_list=['11058.hdf5'],
                                 exists_col='exists')
        df_1 = container.get_df(df_obs + [w])
        df_1['Weight'] = df_1[w] / 27849


        container = HDFcontainer(file_list=['11057.hdf5'],
                                 exists_col='exists')
        df_2 = container.get_df(df_obs + [w])
        df_2['Weight'] = df_2[w] / 12878.



        w = 'NeutrinoWeights.honda2006_gaisserH3a_elbert_v2_numu_conv_nuflux'
        container = HDFcontainer(file_list=['Level4_IC86.2012_nugen_numu.011374.0_100_100Files.clsim-base-4.0.3.0.99_eff.hd5'],
                                 exists_col='exists')
        df_3 = container.get_df(df_obs + [w])
        df_3['Weight'] = df_3[w] / 100



        df = df_1.append(df_2)
        df = df.append(df_3)
        out_file = 'result_all.dat'
    if dataset != 'all':
        df = hdf_container.get_df(df_obs + [w])
        if dataset == '11058':
            df['Weight'] = df[w] / 27849
        elif dataset == '11057':
            df['Weight'] = df[w] / 12878.
        elif dataset == '11374':
            df['Weight'] = df[w] / 200





    result_dict = {}

    result_dict['data_only'] = df_obs
    # Blacklist
    black_list = get_atts_pattern(df_obs, ['I3Even*'])
    sel_att = [o for o in df_obs if o not in black_list]
    result_dict['blacklist'] = black_list

    # Constant Values
    constants = get_constants(df, sel_att)
    sel_att = [o for o in sel_att if o not in constants]
    result_dict['constants'] = constants

    # Constant Values

    # NaN Ratio
    nan_ratio_rel = get_nan_ratio(df, sel_att, weight='Weight', rel=True)
    nan_ratio_abs = get_nan_ratio(df, sel_att, weight='Weight', rel=False)
    result_dict['nan_ratio'] = {}
    result_dict['nan_ratio']['abs'] = nan_ratio_abs
    result_dict['nan_ratio']['rel'] = nan_ratio_rel
    result_dict['nan_ratio']['removed'] = []

    for i, val in zip(nan_ratio_rel.index, nan_ratio_rel):
        if not val < 1.:
            sel_att.remove(i)
            result_dict['nan_ratio']['removed'].append(i)


    threshold = 0.96

    dups, n_dups, thresholds = get_dups_n_thresholds(df,
                                                     sel_att,
                                                     np.linspace(0.1, 1., 91))
    dups_direct = get_dups(df, sel_att, threshold=threshold)
    result_dict['dups'] = {}
    result_dict['dups']['dups'] = dups
    result_dict['dups']['n_dups'] = n_dups
    result_dict['dups']['thresholds'] = thresholds
    result_dict['dups']['removed'] = dups_direct
    result_dict['dups']['threshold'] = threshold
    sel_att = [o for o in sel_att if o not in dups_direct]


    with open(out_file, 'wb') as f:
        cPickle.dump(result_dict, f)
