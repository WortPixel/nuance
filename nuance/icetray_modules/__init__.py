 #!/usr/bin/python
# coding: utf-8

from __future__ import division, print_function
import sys

import numpy as np

try:
	from icecube import dataclasses
	from icecube import dataio
	from icecube import icetray
except:
	raise ImportError('Use this module from within an icetray environment.')


def add_dict_to_frame(frame, value_dict, name):
    '''
    Function to add a dict of doubles to a frame in frame[key][dict_key].
    '''
    I3_double_container = dataclasses.I3MapStringDouble()
    for key in value_dict.keys():
        key.replace('-', '_')
        I3_double_container[key] = value_dict[key]
    frame.Put(name, I3_double_container)


def get_interaction_type(frame, particle, pdg_type=13, first_only=True):
    ''' Get interaction type for chosen pdg type

        Args:
            frame: I3Frame
                Frame to check positions of.
            particle: I3Particle
                Particle (often primary) to obtain infos from.
            first_only: bool
                If True only the first daughter particles are observed.
            pdg_type: int
                PDG encoding of particle to refer the interaction type to
        Returns: List of strings
            List of interactions with respect to given pdg_type.
            E.g. ['cc']
            If the interaction is no cc or nc the pdg_encoding is returned.
    '''
    types = []
    mctree = frame['I3MCTree']
    daughters = mctree.get_daughters(particle)
    for daughter in daughters:
        if daughter.is_neutrino:
            types.append('nc')
        elif daughter.pdg_encoding in (-pdg_type, pdg_type):
            types.append('cc')
        else:
            types.append(daughter.pdg_encoding)
    if first_only:
        types = types[0]
    return types


def get_primary(frame, pdg_type=14):
    ''' Get primary particles of given frame '''
    mctree = frame['I3MCTree']
    ind = [i for i, x in enumerate(mctree.primaries)
           if x.pdg_encoding in (-pdg_type, pdg_type)][0]
    return mctree.primaries[ind]


def get_position(frame, particle, first_only=True):
    ''' Get position(s) of daugher particles

        Args:
            frame: I3Frame
                Frame to check positions of.
            particle: I3Particle
                Particle (often primary) to obtain infos from.
            first_only: bool
                If True only the first daughter particles are observed.
        Returns: List of tuple with x, y, z position for each daughter particle
    '''
    mctree = frame['I3MCTree']
    daughters = mctree.get_daughters(particle)
    positions = [np.array([d.pos.x, d.pos.y, d.pos.z]) for d in daughters]
    if first_only:
        positions = positions[0]
    return positions
