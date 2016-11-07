#!/usr/bin/python
# coding: utf-8
'''
  Author: Philipp Schlunder
  Based on: http://software.icecube.wisc.edu/simulation_trunk/projects/weighting/tutorial.html
  ToDo: 
    - check for energy range of used fluxes
'''

from __future__ import division, print_function

from os.path import isdir
from os.path import join

from glob import glob
from math import cos

from I3Tray import *
import icecube
from icecube import common_variables
from icecube import dataclasses
from icecube import dataio
from icecube import icetray
from icecube import NuFlux
from icecube import phys_services

from icecube.weighting import fluxes
from icecube.weighting.weighting import from_simprod

from nuance.icetray_modules import add_dict_to_frame
from nuance.icetray_modules.generic_attributes import get_primary


class LowEWeightingCalculator(icetray.I3ConditionalModule):
    '''
    Calculate the MC weight for a given frame and store it as 'weight_fluxname'.
    Normalize the produced flux (from within OneWeight) to the new flux and to 
    the used amount of events derived by the used amount of files (n_files).

    Pulses are removed during this step.

    Args:
      frame: Function is a standard i3 function, thus works on the frame
      flux_name: Provide the flux name to be used for weighting
      n_files: Provide number of existing files, `ls -1 | wc -l` might help
      dataset: Used dataset number
      CORSIKA: Descide between neutrino and lepton weighting


    Note:
      It is selfwritten, since neither NuFlux nor NewNuFlux are currently
      supported by icecube.weighting
    '''

    def __init__(self, context):
        icetray.I3ConditionalModule.__init__(self, context)
        self.AddParameter('flux_name',
                          'flux_name',
                          'Provide the flux name to be used for weighting')
        self.AddParameter('n_files',
                          'n_files',
                          'Provide number of existing files, `ls -1 | wc -l`\
                          might help')
        self.AddParameter('dataset',
                          'dataset',
                          'Used dataset number')
        self.AddParameter('CORSIKA',
                          'CORSIKA',
                          'Descide between neutrino and lepton weighting')


    def Configure(self):
        self._flux_name = self.GetParameter('flux_name')
        self._n_files = self.GetParameter('n_files')
        self._dataset = self.GetParameter('dataset')
        self._CORSIKA = self.GetParameter('CORSIKA')


    def Physics(self, frame):
        get_primary(frame)
        if not isinstance(self._flux_name, list):
            self._flux_name = [self._flux_name]
        weights = dict()
        for flux in self._flux_name: 
            weights[flux] = self.get_weight(frame,
                                            flux,
                                            self._n_files,
                                            self._dataset,
                                            self._CORSIKA
                                            )
        add_dict_to_frame(frame, weights, 'weights')
        self.PushFrame(frame)


    def DAQ(self, frame):
        self.PushFrame(frame)


    def Finish(self):
        pass


    def _get_flux_and_norm(self, frame, flux_name, dataset, CORSIKA):
        if isinstance(dataset, str):
            dataset = int(dataset)

        # obtain needed values 
        ptype = frame['I3MCPrimary'].type
        energy = frame['I3MCPrimary'].energy

        if not CORSIKA:
            # obtain needed values 
            zenith = frame['I3MCPrimary'].dir.zenith
            one_weight = frame['I3MCWeightDict']['OneWeight']
            n_events = frame['I3MCWeightDict']['NEvents']

            # look up flux for given values and chosen flux model
            flux = NuFlux.makeFlux(flux_name).getFlux
            flux = flux(ptype, energy, cos(zenith)) * one_weight

            # check if neutrino or anti-neutrino is present
            # need to use neutrino-/anti-neutrino-ratio of chosen data set
            if 'Bar' not in str(ptype):
                family_ratio = 0.7
            else:
                family_ratio = 0.3

            # normalize weight to given amount of files, produced events and
            # particle/anti-particle ratio
            norm = (n_events * family_ratio) 
        else:
            # CORSIKA
            # look up flux for given values and chosen flux model
            flux = getattr(fluxes, flux_name)()
            flux = flux(energy, ptype)

            norm = from_simprod(dataset)
            norm = norm(energy, ptype)

        return flux, norm


    def get_weight(self,
                   frame,
                   flux_name='honda2014_spl_solmin',
                   n_files=1,
                   dataset=None,
                   CORSIKA=False):

        # skip frame if no primary was created
        if 'I3MCPrimary' not in frame:
            return False

        if isinstance(n_files, str):
            n_files = int(n_files)

        flux, norm = self._get_flux_and_norm(frame,
                                             flux_name,
                                             dataset,
                                             CORSIKA)

        # if the normalization is somehow 0, set weight to 0, as well
        if norm == 0:
            weight = 0
        else:
            norm *= n_files
            weight = flux / norm

        #return dataclasses.I3Double(weight)
        return weight


if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option('-i', '--inputfile', dest='input_file')
    parser.add_option('-o', '--outputfile', dest='output_file')
    parser.add_option('-f', '--flux', dest='flux_name',
                      default='honda2014_spl_solmin',
                      help='Set flux_name or list of names to be calculated')
    parser.add_option('-n', '--nfiles', dest='n_files',
                      default='1')
    parser.add_option('-d', '--dataset', dest='dataset')
    parser.add_option('-c', '--corsika', dest='CORSIKA', action='store_true')
    parser.add_option('-t', '--type', dest='type', default='i3')
    parser.add_option('-s', '--subeventstream', dest='sub_event_stream',
                      default='InIceSplit',
                      help='Set the name of the particles sub event name')
    (options, args) = parser.parse_args()

    # create list of unwanted keys to reduce the amount of data
    # that would be sorted out later anyway
    i3_file = dataio.I3File(options.input_file)
    p_frame = i3_file.pop_physics()
    all_keys = p_frame.keys()
    unwanted_keys = filter(lambda x: 'Pulses' in x, all_keys)
    i3_file.close()


    tray = I3Tray()

    files = glob(options.input_file)
    tray.AddModule('I3Reader', 'reader', FilenameList=files)
    if options.CORSIKA:
        from icecube.weighting import CORSIKAWeightCalculator
        weight_name = options.flux_name + '_' + options.dataset
        tray.AddModule(CORSIKAWeightCalculator,
                       weight_name,
                       Dataset = int(options.dataset),
                       Flux    = getattr(fluxes,options.flux_name)(),
                       NFiles  = int(options.n_files),
                       If      = (lambda frame: (not frame.Has(weight_name)))
                       )
    else:
        tray.AddModule(LowEWeightingCalculator,
                       'waiting',
                       flux_name = options.flux_name,
                       n_files   = options.n_files,
                       dataset   = options.dataset,
                       CORSIKA   = options.CORSIKA,
                       If = (lambda frame: (not frame.Has('weights')))
                       )

    # #####################
    # Alternative CORSIKA weight calculation to reduce sql calls:
    # Need to create cache first:
    # ### BEGIN CACHING ###
    # from icecube import weighting
    # import cPickle
    # cache = weighting.SimprodNormalizations()
    # for dataset in (list_of_dataset_numbers):
    #    cache.refresh(dataset)
    # cPickle.dump(cache, open('$I3_BUILD/weighting/resources/dbcache.pickle', 'wb'))
    # ### END CACHING #####
    # from icecube.weighting import CORSIKAWeightCalculator
    # weight_name = options.flux_name + '_' + options.dataset
    # tray.AddModule(CORSIKAWeightCalculator,
    #                weight_name,
    #                Dataset = int(options.dataset),
    #                Flux    = getattr(fluxes,options.flux_name)(),
    #                NFiles  = int(options.n_files),
    #                If      = (lambda frame: (not frame.Has(weight_name)))
    #                )
    # #####################

    tray.AddModule('Delete', 'thin_keys', Keys=unwanted_keys)

    # create output directory it not existent
    if not os.path.isdir(os.path.dirname(options.output_file)):
        os.mkdir(os.path.dirname(options.output_file))

    if options.type == 'i3':
        output_filename = options.output_file
        if not '.i3' in options.output_file:
            output_filename += '.i3.gz'
        else:
            if not '.gz' in output_filename:
                output_filename += '.gz'
        tray.AddModule('I3Writer',
                       'EventWriter',
                       Filename=output_filename,
                       Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ])
    elif options.type == 'hd5':
        from icecube.hdfwriter import I3HDFTableService
        from icecube.tableio import I3TableWriter

        # store everything in hdf5-file
        service = I3HDFTableService(options.output_file + '.hdf5')
        tray.AddModule(I3TableWriter,
                       'writer',
                       tableservice=[service],
                       BookEverything=True,
                       SubEventStreams=[options.sub_event_stream])
    else:
        print('Please use supported type. Currently supported: i3, hd5')

    tray.Add('TrashCan', 'trash')

    tray.Execute()
    tray.Finish()
