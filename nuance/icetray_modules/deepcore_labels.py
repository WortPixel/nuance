#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import os
from glob import glob

from matplotlib.path import Path
import numpy as np
from scipy.spatial import ConvexHull

from I3Tray import *
from icecube import dataclasses, dataio, icetray
from icecube.DeepCore_Filter import DOMS
from nuance.icetray_modules import get_primary


class DetectorByDoms:
    ''' Create fiducial volume by accepting all positions within max_dist
        
        Args:
            dom_positions: List of cartesian dom positions
            max_dist: Maximal distance to allow as fiducial volume around DOM

    '''
    def __init__(self, dom_positions, max_dist=100.):
        self.dom_positions = dom_positions
        self.max_dist = max_dist

    def is_inside(self, v_pos):
        ''' Check if position is within given range of all DOMs belonging to 
        this detector setup.

            Args:
                v_pos: List of cartesian coordinates to check for

            Returns:
                True, if v_pos is within (smaller than) max_dist from any given
                DOM in dom_positions. Using quadratic norm as distance measure.

        '''
        diff = self.dom_positions - v_pos
        dist = np.linalg.norm(diff, axis=1, ord=2)
        return any(dist < self.max_dist)

class DetectorByContour:
    ''' Create a fiducial detector volume by laying a convex hull around DOM
        positions within the x-y-plane, and taking the highest and lowest
        DOMs plus a tolerance as the z-limits.
    '''
    def __init__(self, dom_positions, z_tolerance=0.):
        ''' Creates the fiducial detector volume

            Args:
                dom_positions: list of 3 floats
                    List of cartesian dom positions (x, y, z)
                z_tolerance: float
                    A tolerance value for the z limit in meters, that is added
                    to the max z position and substracted from the lowest.
        '''
        # define fiducial values for z-position
        self._z_pos = [pos[2] for pos in dom_positions]
        self.z_max = max(self._z_pos) + z_tolerance
        self.z_min = min(self._z_pos) - z_tolerance

        # calculate a convex hull around all x-, y-positions
        # as an fiducial area in the x-y-plane
        dom_positions = np.array(dom_positions)
        hull = ConvexHull(dom_positions[:, 0:2])

        # create list of vertices, that allows for a closed polygon
        # need the 1st element as the last to matplotlib.path to create the
        # polygon
        self._vertices = np.vstack([dom_positions[hull.vertices, 0:2],
                                    dom_positions[hull.vertices, 0:2][0]])

        # create polygon of given vertices as fiducial area
        self.xy_plane = Path(self._vertices)


    def is_inside(self, v_pos):
        ''' Test if cartesian position is within the fiducial volume.
            
            Args:
                v_pos: list of 3 floats
                    List of cartesian coordinates of the point to check

            Returns:
                True or false if the point is within the given z range
                (+ tolerance) and within the convex hull around the DOMs in the
                x-y-plane.
        '''
        if self.z_min < v_pos[2] < self.z_max and \
           self.xy_plane.contains_point(v_pos):
            return True
        else:
            return False

class DeepCoreLabels(icetray.I3ConditionalModule):
    def __init__(self, context):        
        # load dom lists 
        self.dc_oms = DOMS.DOMS("IC86").DeepCoreFiducialDOMs
        self.ext_dc_oms = DOMS.DOMS("IC86EDC").DeepCoreFiducialDOMs
        icetray.I3ConditionalModule.__init__(self, context)
        self.AddParameter('EXTENDED',
                          'Calculate Label for extended deepcore region is set\
                           to true',
                          False)
        self.AddParameter('DETECTOR_BUILD_ONLY',
                          'Only create file with detector build info.',
                          False)
        self.AddParameter('NEUTRINO_TYPE',
                          'PDG encoding for neutrino to check interaction from',
                          14)


    def Configure(self):
        self.detector_parts = {}
        self._EXTENDED = self.GetParameter('EXTENDED')
        self._DETECTOR_BUILD_ONLY = self.GetParameter('DETECTOR_BUILD_ONLY')
        self._NEUTRINO_TYPE = int(self.GetParameter('NEUTRINO_TYPE'))


    def setup_detector_parts(self, geometry_frame,
            detector=DetectorByContour):
        ''' Get cartesian detector coordinates to given DOM list from GCDfile.
    
            Args:
                gemetry_frame: GCD frame containing map between omkeys and
                               coordinates.
        '''
        dom_lists = {'deepcore': self.dc_oms}
        if self._EXTENDED:
            dom_lists['deepcore_ext'] = self.ext_dc_oms
        i3geometry = geometry_frame['I3Geometry'].omgeo
        for configuration, dom_list in dom_lists.items():
            dom_pos = []
            for om in dom_list:
                dom_pos.append(i3geometry[om].position)
            self.detector_parts[configuration] = detector(dom_pos)


    def Finish(self):
        ''' Create detector build of given detector configuration and export
            it into a file '''
        if self._DETECTOR_BUILD_ONLY:
            if sys.version_info[0] >= 3:
                import pickle
            else:
                import cPickle as pickle
            pickle.dump(self.detector_parts, open('detector.pickle', 'wb'))


    def Geometry(self, frame):
        ''' Create the DOM dict '''
        self.dom_dict = self.setup_detector_parts(frame)
        self.PushFrame(frame)


    def Physics(self, frame):
        ''' Check if muon from CC is created within detection volumes '''
        if len(self.detector_parts.keys()) == 0:
        	raise IOError('You need to provide a gcd file.')
        primary = get_primary(frame, pdg_type=self._NEUTRINO_TYPE)
        # neutrino type - 1 = lepton flavour of given neutrino type
        in_parts = self.is_cc_in_detector(frame, primary,
                                          pdg_type=self._NEUTRINO_TYPE-1)
        if isinstance(in_parts, list):
            in_deepcore = True if 'deepcore' in in_parts else False
            if self._EXTENDED:
                in_deepcore_ext = True if 'deepcore_ext' in in_parts else False
        else:
            in_deepcore = False
            if self._EXTENDED:
                in_deepcore_ext = False
        frame.Put('cc_in_deepcore', icetray.I3Bool(in_deepcore))
        if self._EXTENDED:
            frame.Put('cc_in_deepcore_ext', icetray.I3Bool(in_deepcore_ext))
        self.PushFrame(frame)


    def is_cc_in_detector(self, frame, particle, pdg_type=13):
        ''' Check if daughter particles from particle create CC muons within
            detection volumes

            Args:
                particle: I3Particle whose secondaries (daughters) should be
                          checked.
                pdg_type:
                    PDG encoding for particles. 11 e, 12 nue, 13 mu, 14 numu,
                    15 tau, 16 nutau
            Returns:
                List of detector setups containing the CC muon.
        '''
        mctree = frame['I3MCTree']
        # get daughter particles from interaction
        particle_daughters = mctree.get_daughters(particle)
        if len(particle_daughters) != 0:  # particle.dir.zenith < np.pi/2.
            for daughter in particle_daughters:
                # NC interaction
                if daughter.is_neutrino is True:
                    return self.is_cc_in_detector(frame, daughter)
                elif daughter.pdg_encoding in (-pdg_type, pdg_type):
                    # get position of daughter particle
                    v_pos = np.array([daughter.pos.x,
                                      daughter.pos.y,
                                      daughter.pos.z])
                    # check if it is within given detector configurations
                    in_parts = [key for key, part in
                                self.detector_parts.iteritems()
                                if part.is_inside(v_pos)]
                    return in_parts
                # Hadron?
                else:
                    return []
        else:
            return []


if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option('-i', '--inputfile', dest='input_file')
    parser.add_option('-o', '--outputfile', dest='output_file')
    parser.add_option('-g', '--gcdfile', dest='gcd_file')
    parser.add_option('-e', '--extended', dest='extended', action='store_true')
    (options, args) = parser.parse_args()

    tray = I3Tray()
    files = glob(options.input_file)
    files = [options.gcd_file] + files 
    tray.AddModule('I3Reader', 'reader', FilenameList=files)
    tray.AddModule(DeepCoreLabels, 'labelmaker', EXTENDED=options.extended)

    # create output directory it not existent
    #if not os.path.isdir(os.path.dirname(options.output_file)):
    #    os.mkdir(os.path.dirname(options.output_file))

    tray.AddModule('I3Writer',
                   'EventWriter',
                   Filename=options.output_file + '.i3.gz',
                   Streams=[icetray.I3Frame.Physics,icetray.I3Frame.DAQ])

    tray.Add('TrashCan', 'trash')

    tray.Execute(100)
    tray.Finish()
