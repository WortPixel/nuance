#!/usr/bin/env python
# coding: utf-8
'''
.. module:: datahandler
    :platform: Unix

.. moduleauthor:: Philipp Schlunder <philipp.schlunder@udo.edu>

'''

from __future__ import division, print_function
import os
from os import listdir
from os.path import expandvars
from os.path import isdir
from os.path import join
import subprocess

import copy
from glob import glob
import json

from functools import reduce

import numpy as np
from tqdm import tqdm

from .parser import check_type, is_ending_in
from .i3hdf_to_df import HDFContainer, ObservableName

# TO DO: export these to config file
DB_CACHE = expandvars('$THESIS/scripts/database/')
DB_SUFFIX = "dataset"
DATA_DIR = expandvars('$THESIS/data/')
HDF_SUFFIX = ['h5', 'hd5', 'hdf5']
I3_SUFFIX = ['i3', 'i3.gz', 'i3.bz2']


def create_folder(path):
    if not os.path.isdir(path):
        subprocess.call(['mkdir', '-p', path])


def get_burnsample(path, months=None):
    ''' Provide list of paths to hd5 files with run numbers ending with zero
    
        Args:
            months: list of strings
            Each string with month numbers (MM) to select runs from.

        Returns:
            List of paths to given burnsample runs

        TODO get runs from goodrunlist and parse them, get livetimes and gcd's
    '''
    result = []
    for date in listdir(path):
        if months is not None:
            if not any([date.startswith(month) for month in months]):
                continue
        for run in listdir(join(path, date)):
            if run.startswith('Run') and run.endswith('0'):
                result.append(join(path, date, run))
    return result


class DataSetHandler(object):
    ''' A handler for multiple data sets'''
    def __init__(self, db_dir=DB_CACHE, data_dir=DATA_DIR, settings=None):
        ''' Scan database for all available dataset files
            
            Args:
                db_dir: 
                    Directory holding the data base cache files
                data_dir:
                    Root directory of data sets
                settings:
                    Path to general setting file concerning all data sets
        '''
        if not settings is None:
            with open(settings, 'r') as s:
                json_file = json.load(s)
                self._blacklists = {k: v for k, v in json_file.items() \
                                    if 'blacklist' in k}
                self._loading_properties = json_file['datasets']
        else:
            self._blacklists = dict()
            self._loading_properties = dict()
        self._datasets = dict()
        try:
            self._dataset_paths = glob(join(db_dir, '*.' + DB_SUFFIX))
            if len(self._dataset_paths) == 0:
                print('No file with .dataset ending found.')
        except:
            raise IOError("Can't find data sets in {}. Please provide a valid \
                path.".format(db_dir))

        path_dict = {}
        for path in self._dataset_paths:
            with open(path, 'r') as current_file:
                json_file = json.load(current_file)
                data_type = json_file['type']
                path_dict[data_type] = path
                self._datasets[data_type] = DataSet(json_file,
                                                            data_dir=data_dir)
                try:
                    self._datasets[data_type]._weight_names = self._loading_properties[data_type]['weights']
                except:
                    pass
        self._dataset_paths = path_dict
        self._observables = None


    @property
    def datasets(self):
        return self._datasets.keys()


    @property
    def observables(self):
        ''' Get intersection of all observables '''
        if self._observables is None:
            # TODO: parallelize observable loading
            all_attributes = [dataset.observables(**self._blacklists) \
                              for dataset in tqdm(self._datasets.values(),
                                desc="Scanning datasets for observables ") \
                              if not ":" in dataset.path]
            self._observables = list(reduce(set.intersection,
                                     map(set, all_attributes)))
            self._observables = list(map(str, self._observables))
            self._observables = sorted(self._observables)
        return self._observables


    def load_all(self, keys=None, skip=None, **kwargs):
        ''' Load all data sets with the given options in kwargs '''
        if not skip is None:
            if isinstance(skip, str):
                skip = list(skip)
        if keys is None:
                keys = copy.copy(self.observables)
        for dataset, data in tqdm(self._datasets.items(), desc="Datasets "):
            if not skip is None and not dataset in skip:
                # TODO: parallelize loading
                temp_keys = copy.copy(keys)
                n_files = self._loading_properties[dataset]['n_files']
                props = self._loading_properties[dataset]
                if 'keys' in props.keys():
                    temp_keys += props['keys']
                if 'weights' in props.keys():
                    temp_keys += props['weights']
                data.load(keys=temp_keys, n_files=n_files, **kwargs)


    def __getitem__(self, dataset_name):
        return self._datasets[dataset_name]


    def __str__(self):
        ''' Print list of data sets type: name '''
        if len(self._datasets) > 0:
            output = 'Data sets: '
            list_of_datasets = ', '.join(['{}: {}'.format(dataset,
                self._datasets[dataset]['name']) for dataset \
                in self._datasets.keys()])
            output = output + list_of_datasets
        else:
            output = 'No data sets present.'
        return output


    def update(self):
        ''' Update the json file '''
        for set_name, dataset in self._datasets.items():
            with open(self._dataset_paths[set_name],'w') as output:
                json.dump(dataset.properties, output, sort_keys=True, indent=4,
                          separators=(',', ': '))
            print('Wrote properties from {} to {}'.format(
                set_name, self._dataset_paths[set_name]))
            #print('Problem writing properties of {}'.format(dataset.name))


class DataSet(object):
    ''' An object handling the data and meta-data of a given dataset.
        
        Args:
            size_on_disc: Size of dataset on disc, load only if called and
                not in database
            size: Size of file loaded into memory
    '''
    def __init__(self, dataset, data_dir=DATA_DIR):
        # load properties from dataset json file
        if not isinstance(dataset, dict):
            if isinstance(dataset, str):
                with open(path, 'r') as current_file:
                    json_file = json.load(current_file)
                    dataset = json_file
            else:
                raise TypeError('Dataset must be a dict from a json file \
                    or a path to a json file to load.')
        self.properties = dataset

        self._files = dataset['files'] if 'files' in dataset else None
        
        self.blacklist = dataset['blacklist'] if 'blacklist' in dataset \
                                              else None
        self.data = None
        self._data_dir = data_dir
        self.files_loaded = None
        self.key_log = dict()
        self.loaded = False 
        self.n_files = check_type(dataset['n_files'], int, default=1.)
        self.name = dataset['name']
        self._observables = None
        if 'local_path' in dataset.keys():
            self.path = check_type(dataset['local_path'], str)
        else:
            self.path = check_type(dataset['remote_path'], str)
        self.path = expandvars(self.path)
        self.source = dataset['source_path'] if 'source_path' in dataset \
                                             else None
        self.systematics = dataset['systematics'] if 'systematics' in dataset \
                                                  else None
        self.type = dataset['type']
        self._weights = None
        self._weight_names = None


    def __getitem__(self, observable):
        if self.loaded:
            return self.data[observable].values
        else:
            print("{} hasn't been loaded, yet.".format(self.name))
            return None


    def __str__(self):
        output = ''
        for key, value in self.properties.items():
            output += "{}: {}\n".format(key, value) 
        return output

    def _get_from_remote(self,
                         hostname,
                         remote_dir,
                         filelist_only=False,
                         filelist=None,
                         local_dir=None,
                         ):
        ''' Connect to remote location to get/download filelist

            Args:
                hostname: str
                    SSH Hostname of the remote server
                remote_dir: str
                    Path of the source directory
                filelist_only: bool
                    Get only a list of all files in the remote dir, or download
                    it
                local_dir: str
                    Path to local download destination

            Warning:
                Currently not working with Python3
        '''
        # similar to http://stackoverflow.com/a/20381739 and
        # https://gist.github.com/tell-k/4943359#file-paramiko_proxycommand_sample-py-L11
        from contextlib import closing
        import paramiko

        config = paramiko.SSHConfig()

        with open(expandvars('$HOME/.ssh/config')) as config_file:
           config.parse(config_file)
        host = config.lookup(hostname)

        # connect
        with closing(paramiko.SSHClient()) as client:
            # load matching key
            client.load_system_host_keys()
            client.connect(host['hostname'],
                           username=host['user'],
                           key_filename=host['identityfile'],
                           sock=paramiko.ProxyCommand(host.get('proxycommand')))
            with closing(client.open_sftp()) as sftp:
                sftp.chdir(remote_dir)
                if filelist_only:
                    remote_filelist = sftp.listdir()
                    return np.array(remote_filelist)
                else:
                    if not local_dir is None:
                        create_folder(local_dir)
                        # cd to local destination directory
                        os.chdir(local_dir)
                    # download all files in it to local_dir directory
                    for filename in tqdm(filelist,
                                         desc="Downloading from Remote"):
                        try:
                            if not os.path.isfile(filename):
                                sftp.get(join(remote_dir, filename), filename)
                            else:
                                print("{} already exists".format(filename))
                        except IOError as e:
                            print("IOError occured, this seems to happen sometimes.")
                            print(e)


    def _get_weight_names(self, observables, weight_tab=None):
        ''' Get weight names from the available weights in the data set '''
        if weight_tab is None:
            weight_tab = "weights"
        weight_names = []
        col_blacklist = ["Run", "Event", "SubEvent", "SubEventStream", "exists"]
        for attr in observables:
            if isinstance(attr, str):
                tab, col = attr.split('.')
            else:
                # type should be i3hdf_to_df.ObservableName
                tab = attr.tab
                col = attr.col
            if tab == weight_tab and not col in col_blacklist:
                weight_names.append(str(attr))
        return weight_names


    def _load_from_hdf(self, files, keys=None, exists_col=None,
                       observables_only=False, **kwargs):
        if ':' in self.path:
            raise NotImplementedError("Files are on a remote location. Loading to cache from remote isn't supported, yet.")
        file_list = [join(self.path, filename) for filename in files]
        try:
            container = HDFContainer(exists_col=exists_col, file_list=file_list)
        except:
            container = None

        if not container is None:
            if not observables_only:
                if keys is not None:
                    self.data = container.get_df(keys)
                    self._observables = keys
                else:
                    if self._observables is None:
                        self._observables = container.get_observables(
                            check_all=False, **kwargs)
                    self.data = container.get_df(self._observables)
                self.loaded = True
            else:
                self._observables = container.get_observables(check_all=False,
                                                              **kwargs)
        else:
            print("Error while loading")


    def _load_from_i3(self, files, keys):
        file_list = [join(self.path, filename) for filename in files]
        if keys is None:
            print("Please provide keys, this tool isn't ment to read all i3 attributes.")
        raise NotImplementedError("I3 file handling, yet to be implemented.")   


    @property
    def files(self, path=None):
        ''' List of files in path

            Args:
                path: If None self.path is used, else path
            Returns:
                List of files in path
        '''
        if self._files is None:
            path = self.path if path is None else path
            if ':' in path:
                # hostname available
                hostname, remote_dir = path.split(':')
                self._files = self._get_from_remote(
                    hostname,
                    remote_dir,
                    filelist_only=True)
            else:
                self._files = np.array(listdir(path))
            # only store files that aren't in the blacklist
            blacklist = self.blacklist if not self.blacklist is None else []
            blacklist.append('.DS_Store')
            self._files = self._files[~np.in1d(self._files, blacklist)]
        return self._files


    @property
    def size_on_disk(self):
        if 'size_on_disk' in self.properties.keys():
            self._size_on_disk = int(self.properties['size_on_disk'])
        else:
            if isdir(self.path):
                self._size_on_disk = int(subprocess.check_output(['du', '-s',
                    self.path]).split('\t')[0])
            else:
                self._size_on_disk = 0
                raise IOError('{} is no directory'.format(self.path))
        return self._size_on_disk


    @property
    def weights(self):
        ''' Stores the weights of a given data set '''
        if self._weights is None:
            if self.loaded:
                self._weights = self.data[self.weight_names]
            else:
                raise IOError("Data should be loaded first.")
        return self._weights

    @weights.setter
    def weights(self, value):
        self._weights = value


    @property
    def weight_names(self):
        ''' Retrieve weight names from data '''
        if self._weight_names is None:
            self._weight_names = self._get_weight_names(self.observables(),
                                                        weight_tab="weights")
        return self._weight_names


    def close(self):
        ''' Cut reference to data in order to free memory '''
        self.data = None
        self.loaded = False


    def drop(self, keys, reason):
        ''' Remove keys from data and write dropped keys to dataset

            Args:
                keys: list
                    List of strings with keys to remove.
                reason: str
                    Reaseon for dropping the key. Is stored in dataset.
        '''
        if not isinstance(keys, list):
            keys = [keys]
        if not reason in keys:
            self.key_log[reason] = keys
        else:
            self.key_log[reason] += keys
        try:
            self.data = self.data.drop(keys, axis=1)
            self._observables = [o for o in self.observables if o not in keys]
        except ValueError:
            print('Tried to remove some attributes, that didn\'t exist')


    def load(self, keys=None, n_files=None, to_cache=True, exists_col=None,
             weight_tab=None, **kwargs):
        ''' Load i3 or hdf5 file in memory or on disc

            Args:
                keys: List of attributes to load. Attributes are (often)
                    reconstructions hence groups of properties.
                    Use attribute.property to only load these.
                n_files: Number of files to load from available files in 
                    self.path. None loads all.
                to_cache: Flag if files should be loaded (from remote) to 
                    client, or into memory.
                exists_col: Column with values determining if a algorithm worked
                    If exists is 0 all other attributes for the event are set
                    to NaN.
                kwargs:
                    Surpass attributes to i3hdf_to_df.get_observables e.g.
                    blacklist_obs=['LineFit.x'], blacklist_tabs=['SplineMPE']
                    or blacklist_cols=['exists']

            Returns:
                Numpy array of all keys to load

            Examples:
                >>> load(keys=['LineFit.energy'])

        '''
        if to_cache is True:
            files = np.array(self.files)
        elif to_cache is False:
            import sys
            if sys.version_info.major > 2:
                raise NotImplementedError("Since paramiko only works with python 2 "\
                    "this function doesn't support python 3, as well.")
            # need to get file list from remote
            hostname, remote_dir = self.properties['remote_path'].split(':')
            files = np.array(self._get_from_remote(
                        hostname,
                        remote_dir,
                        filelist_only=True))
        if n_files is not None:
            # get n_files random indices for number of files to load
            #rand_ind = np.random.randint(0, len(files), n_files)
            rand_ind = np.random.choice(np.arange(0, len(files)), n_files,
                                        replace=False)
            files = files[rand_ind]
            print("Loading the following files from {}:".format(self.path))
            print(files)

        if to_cache is True:
            if is_ending_in(HDF_SUFFIX, files):
                self._load_from_hdf(files, keys, exists_col=exists_col,
                                    **kwargs)
                self._weights = self.data[self.weight_names]
            elif is_ending_in(I3_SUFFIX, files):
                self._load_from_i3(files, keys)
            else:
                raise TypeError("File ending unknown.")
        elif to_cache is False:
            if 'local_path' in self.properties.keys():
                local_path = expandvars(self.properties['local_path'])
            else:
                local_path = join(self._data_dir, self.name)
                self.properties['local_path'] = local_path
                self.path = self.properties['local_path']
                
            #hostname, remote_dir = self.properties['remote_path'].split(':')
            self._files = self._get_from_remote(
                    hostname,
                    remote_dir,
                    filelist_only=False,
                    filelist=files,
                    local_dir=local_path)


    def observables(self, **kwargs):
        if self._observables is None:            
            if len(kwargs.keys()) > 0:
                self._load_from_hdf(self.files, observables_only=True, **kwargs)
            else:
                self._load_from_hdf(self.files, observables_only=True)
        return self._observables
