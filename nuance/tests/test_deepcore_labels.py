# coding:utf-8
from __future__ import print_function

import os
try:
    from subprocess import run
except ImportError:
    from subprocess import call as run
import unittest

import nuance
from nuance.icetray_modules import deepcore_labels as dl

from I3Tray import *
from icecube import dataclasses
from icecube import dataio
from icecube import icetray


class TestDeepCoreLabels(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(nuance.__file__)
        self.path = os.path.join(self.path, 'tests')
        print(self.path)
        if not os.path.isdir(os.path.join(self.path, 'test')):
            os.mkdir(os.path.join(self.path, 'test'))
        self.i3file = os.path.expandvars('$THESIS/data/i3/cc_in_dc_test.i3.gz')
        self.gcdfile = os.path.expandvars('$THESIS/data/i3/GeoCalibDetectorSta'\
            'tus_2013.56429_V1_Modified.i3.gz')
        if not os.path.isfile(self.i3file):
            inp = input if sys.version_info[0] >= 3 else raw_input
            self.i3file = inp('Please provide path to an low E i3 file: ')
        if not os.path.isfile(self.gcdfile):
            self.gcdfile = inp('Please provide matching gcd file: ')


    def tearDown(self):
        run(['rm', '-rf', 'test'])
        self.path = None
        self.i3file = None
        self.gcdfile = None


class TestExistance(TestDeepCoreLabels):
    def runTest(self):
        tray = I3Tray()
        tray.AddModule('I3Reader', 'reader', Filenamelist=[self.gcdfile,
                                                           self.i3file])
        tray.AddModule(dl.DeepCoreLabels,'labelmaker')
        tray.AddModule('I3Writer', 'writer', Filename=os.path.join(
            self.path,
            'test/ouput.i3.gz'), 
            Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ])
        tray.AddModule('TrashCan', 'can')
        tray.Execute(10)
        del tray
        i3file = dataio.I3File(os.path.join(self.path, 'test/ouput.i3.gz'))
        p_frame = i3file.pop_physics()
        self.assertTrue('cc_in_deepcore' in p_frame, 'cc_in_deepcore was not'\
        ' found in i3file after module execution')
        del i3file
        del p_frame


class CreateTestPlots(TestDeepCoreLabels):
    def _get_data(i3file):
        frames = []
        # open i3 file
        i3file = dataio.I3File(i3file)
        # get interactions and positions of all frames (including all daughters)
        pframe = i3file.pop_physics()
        while pframe != None:
            # CC, NC or other?
            interactions = get_interaction_type(pframe)
            positions = get_positions(pframe)
            frames.append((positions, interactions))
        return frames

    def runTest(self):
        self.data = self._get_data(self.i3file)
        self._plot_top_view(self.data)







if __name__ == '__main__':
    unittest.main()
