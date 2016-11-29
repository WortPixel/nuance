# coding:utf-8
from __future__ import print_function

import os
from distutils.util import strtobool
try:
    from subprocess import run
except ImportError:
    from subprocess import call as run
import matplotlib as mpl
import numpy as np
import pandas as pd
import unittest

import nuance
from nuance.icetray_modules import deepcore_labels as dl
from nuance.icetray_modules import get_interaction_type
from nuance.icetray_modules import get_primary
from nuance.icetray_modules import get_position

from I3Tray import *
from icecube import dataclasses
from icecube import dataio
from icecube import icetray

inp = input if sys.version_info[0] >= 3 else raw_input


class TestDeepCoreLabels(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(nuance.__file__)
        self.path = os.path.join(self.path, 'tests')
        print(self.path)
        if not os.path.isdir(os.path.join(self.path, 'test')):
            os.mkdir(os.path.join(self.path, 'test'))
        self.i3_file = os.path.expandvars('$THESIS/data/i3/cc_in_dc_test.i3.gz')
        self.gcd_file = os.path.expandvars('$THESIS/data/i3/GeoCalibDetectorSt'\
            'atus_2013.56429_V1_Modified.i3.gz')
        if not os.path.isfile(self.i3_file):
            self.i3_file = inp('Please provide path to an low E i3 file: ')
        if not os.path.isfile(self.gcd_file):
            self.gcd_file = inp('Please provide matching gcd file: ')


    def tearDown(self):
        run(['rm', '-rf', 'test'])
        self.path = None
        self.i3_file = None
        self.gcd_file = None


class TestExistance(TestDeepCoreLabels):
    def runTest(self):
        tray = I3Tray()
        tray.AddModule('I3Reader', 'reader', Filenamelist=[self.gcd_file,
                                                           self.i3_file])
        tray.AddModule(dl.DeepCoreLabels,'labelmaker')
        tray.AddModule('I3Writer', 'writer', Filename=os.path.join(
            self.path,
            'test/ouput.i3.gz'), 
            Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ])
        tray.AddModule('TrashCan', 'can')
        tray.Execute(10)
        del tray
        i3_file = dataio.I3File(os.path.join(self.path, 'test/ouput.i3.gz'))
        p_frame = i3_file.pop_physics()
        self.assertTrue('cc_in_deepcore' in p_frame, 'cc_in_deepcore was not'\
        ' found in i3_file after module execution')
        del i3_file
        del p_frame


class CreateTestPlots(TestExistance):
    ''' Create test plots from existing i3 files with deepcore labels '''
    def _get_data(self, i3_file):
        ''' Reads interaction type and position of a given i3 file

            Args: 
                i3_file: icecube.dataio.I3File
                    I3 File with i3 frames to read.
            Returns:
                Pandas DataFrame with x, y, z, type columns of interactions.
        '''
        interactions = []
        positions = []
        label = []
        # open i3 file
        i3_file = dataio.I3File(i3_file)
        # get interactions and positions of all frames (including all daughters)
        pframe = i3_file.pop_physics()
        while i3_file.more():
            # obtain primary
            primary = get_primary(pframe)
            # CC, NC or other?
            interactions.append(get_interaction_type(pframe, primary))
            positions.append(get_position(pframe, primary))
            label.append(pframe['cc_in_deepcore'])
            pframe = i3_file.pop_physics()
        positions = np.array(positions)
        print(positions.shape)
        frames = pd.DataFrame(np.array([positions[:,0],
                                        positions[:,1],
                                        positions[:,2],
                                        interactions,
                                        label]).swapaxes(0, 1),
                              columns=['x', 'y', 'z', 'type', 'label'])
        print(len(frames['label']))
        print(frames[0])
        self._data = frames


    def _get_detector(self, gcd_file, output_file='detector.pickle'):
        ''' Generate detector contour using DeepCoreLabels
            Args:
                gcd_file: dataio.I3File
                I3File with at least a geometry frame.
            Returns: dict
                DOM positions of detector contours
        '''
        create_new = True
        if os.path.isfile(output_file):
            create_new = inp('{} already exists. '\
                             'Create new? [y/n] '.format(output_file))
            create_new = strtobool(create_new)
        if create_new:
            tray = I3Tray()
            tray.AddModule('I3Reader', 'reader', Filename=gcd_file)
            # create output_file in current folder
            tray.AddModule(dl.DeepCoreLabels, 'labelmaker',
                DETECTOR_BUILD_ONLY=True, EXTENDED=False)
            tray.AddModule('TrashCan','can')
            tray.Execute()
            tray.Finish()
            # load detector file to return it 
        if sys.version_info[0] >= 3:
            import pickle
        else:
            import cPickle as pickle
        self._detector = pickle.load(open(output_file, 'rb'))


    def _plot_view(self, view='side'):
        ''' Plot top or side view of the detector with labeled events in it '''
        from matplotlib.path import Path
        from matplotlib import pyplot as plt
        from matplotlib import style
        from icecube.DeepCore_Filter import DOMS
        style.use('ggplot')

        # get DOMs considered as DeepCore
        doms = DOMS.DOMS('IC86').DeepCoreFiducialDOMs
        # get DOM - cartesian position 
        gcd = dataio.I3File(self.gcd_file)
        gframe = gcd.pop_frame()
        while gframe.Stop != icetray.I3Frame.Geometry:
            gframe = gcd.pop_frame()
        dom_positions = np.array([gframe['I3Geometry'].omgeo[dom].position \
                                  for dom in doms])

        folder = 'plots'
        if not os.path.isdir(folder):
            os.mkdir(folder)
        for config in self._detector.keys():
            if view == 'top':
                hull = self._detector[config].xy_plane.vertices
                # plot MC event positions
                mask = self._data.type != 'nc'
                plt.plot(self._data.x[mask], self._data.y[mask], 'b+',
                         label='nc')
                mask = self._data.type == 'cc'
                plt.plot(self._data.x[mask], self._data.y[mask], 'r+',
                         label='cc')
                # plot label boarder as contour
                plt.plot(hull[:,0], hull[:,1], 'k-', label='Contour')
                # plot DOM positions
                plt.plot(dom_positions[:,0], dom_positions[:,1], 'o',
                         label='DOMs')
                plt.xlabel('x')
                plt.ylabel('y')
                plt.legend(loc="best")
                plt.savefig(os.path.join(folder, config + '_' + view + '.pdf'))
                plt.clf()
            elif view == 'side':
                hull = self._detector[config]
                # plot MC event positions
                mask = self._data.type != 'nc'
                plt.plot(self._data.x[mask], self._data.z[mask], 'b+',
                         label='nc')
                mask = self._data.type == 'cc'
                plt.plot(self._data.x[mask], self._data.z[mask], 'r+',
                         label='cc')
                # plot label boarder as contour
                x = hull.xy_plane.vertices[:,0]
                z_min = np.full_like(x, hull.z_min)
                z_max = np.full_like(x, hull.z_max)
                plt.plot(x, z_min, 'k-', label='Contour')
                plt.plot(x, z_max, 'k-')
                # plot DOM positions
                plt.plot(dom_positions[:,1], np.full_like(dom_positions[:,1],
                         hull.z_max), 'o', label='DOMs')
                plt.xlabel('x')
                plt.ylabel('z')
                plt.legend(loc="best")
                plt.savefig(os.path.join(folder, config + '_' + view + '.pdf'))
                plt.clf()
            else:
                raise ValueError('Provided view option is not supported,'\
                                 'use: top, side')


    def runTest(self):
        self._get_detector(self.gcd_file)
        self._get_data(self.i3_file)
        self._plot_view(view='top')
        self._plot_view(view='side')



if __name__ == '__main__':
    unittest.main()
