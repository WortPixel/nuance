 #!/usr/bin/python
# coding: utf-8

from __future__ import division, print_function
import sys

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
