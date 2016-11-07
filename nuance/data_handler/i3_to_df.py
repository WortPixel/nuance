#!/usr/bin/env python
# coding: utf-8

import numpy as np

from I3Tray import *
import icecube
from icecube import icetray
from icecube import dataclasses
from icecube import dataio
from icecube import simclasses
from icecube import phys_services
from icecube import linefit
from icecube import gulliver
from icecube import common_variables


def main(file_list, keys):
	data = dict.fromkeys(keys, [])
	for file_name in file_list:
		i3_file = dataio.I3File(file_name)
    	p_frame = i3_file.pop_physics()
    	while p_frame != None:
    		for key in keys:
    			attribute, column = key.split('.')
    			data[key].append(p_frame[attribute].get(column))