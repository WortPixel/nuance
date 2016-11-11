# coding:utf-8
from __future__ import print_function

import os
try:
    from subprocess import run
except ImportError:
    from subprocess import call as run
import unittest

from nuance.icetray_modules import deepcore_labels as dl

from I3Tray import *
from icecube import dataclasses
from icecube import dataio
from icecube import icetray


class TestDeepCoreLabels(unittest.TestCase):
    def setUp(self):
        if not os.path.isdir('test'):
            os.mkdir('test')
        i3file = '$THESIS/data/i3/L3.14600.000483.InIcePulses.weighted.i3.gz'
        gcdfile = '$THESIS/data/i3/GeoCalibDetectorStatus_2013.56429_V1_Modified.i3.gz'
        if not os.path.isfile(os.path.expandvars(i3file)):
            i3file = input('Please provide path to an i3 file: ')
        if not os.path.isfile(os.path.expandvars(gcdfile)):
            gcdfile = input('Please provide matching gcd file: ')


    def test_DetectorByDoms(self):
        pass


    def test_DetectorByContour(self):
        pass


    def test_is_cc_in_detector(self):
        pass


    def test_general_attribute_insertion(self):
        tray = I3Tray()
        tray.AddModule('I3Reader', 'reader', Filenamelist=[
            'test/GeoCalibDetectorStatus_2013.56429_V1_Modified.i3.gz',
            'test/L3.14600.000483.InIcePulses.weighted.i3.gz'])
        tray.AddModule(dl.deepcore_labels,'labelmaker')
        tray.AddModule('I3Writer', 'writer', Filename='ouput.i3.gz',
                       Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ])
        tray.AddModule('TrashCan', 'can')
        tray.Execute(10)
        del tray
        i3file = dataio.I3File('test/ouput.i3.gz')
        p_frame = i3file.pop_physics()
        self.assertTrue('cc_in_deepcore' in p_frame)
        del i3file
        del p_frame


    def tearDown(self):
        run(['rm', '-rf', 'test'])


if __name__ == '__main__':
    unittest.main()
