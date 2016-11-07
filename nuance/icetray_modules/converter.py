#!/usr/bin/env python
# coding: utf-8
'''
Convert i3 files into root or hdf5 files.
'''

import copy
import os
import sys

from I3Tray import *

# Load all libraries needed to type conversions
# Types not recognized won't be converted
from icecube import icetray
from icecube import dataclasses
from icecube import dataio
from icecube import simclasses
from icecube import phys_services
from icecube import linefit
from icecube import cramer_rao
from icecube import gulliver
from icecube import common_variables
from icecube.tableio import I3TableWriter
from icecube.tableio import I3CSVTableService
from icecube.hdfwriter import I3HDFTableService
from icecube.rootwriter import I3ROOTTableService

from nuance.icetray_modules import generic_attributes


def convert(inputpath,
            outputfile,
            file_type='hdf5',
            sub_event_stream='InIceSplit',
            verbose=False,
            generateID=False):
    '''
    Convert files from i3 to hdf5 or root

    Args:
        inputpath: Inputpath to be scanned for i3 files, input file works, too
        outputfile: Outputpath for the converted file
        file_type: Choose the output format between root and hdf5
        sub_event_stream: Provide the i3 subeventstream to use
        verbose: Provide verbose output
        generateID: Generate a new unique event id

    Returns:
        Nothing
    '''
    # give output if requested
    if verbose:
        print 'Input folder is "', inputpath
        print 'Output file is "', outputfile
        print 'Outputformat is "', file_type

        if generateID:
            print 'P-frame-based ID will be added to "I3EventHeader".'

    # list of possible i3 endings
    i3_endings = ['i3', 'i3.gz', 'i3.bz2'] 

    tray = I3Tray()

    # create list of all files of input path
    i3_files = []
    
    # differentiate between a given path or filename
    if os.path.isdir(inputpath):
        root, subdirs, _ = os.walk(inputpath).next()
        if verbose:
            print("Subdirs:")
            print(subdirs)
            print("Filenames:")
        for subdir in subdirs:
            for filename in os.listdir(os.path.join(root, subdir)):
                if verbose:
                    print(filename)
                if any([filename.endswith(ending) for ending in i3_endings]):
                    i3_files.append(os.path.join(*[root, subdir, filename]))
        tray.AddModule('I3Reader', 'reader', FilenameList = i3_files)
    else:
        # seems to be a single file
        outputfile = os.path.join(
                os.path.dirname(outputfile),
                os.path.basename(inputpath[:inputpath.find('.i3')]))
        print(outputfile)
        if any([inputpath.endswith(ending) for ending in i3_endings]):
            tray.AddModule('I3Reader', 'reader', Filename = inputpath)
        else:
            print('File format not supported')

    # create output path if necessary
    if not os.path.isdir(os.path.dirname(outputfile)):
        os.makedirs(os.path.dirname(outputfile))

    # choose output file_type
    if file_type == "root":
        service = I3ROOTTableService(outputfile + '.root', 'master_tree')
        if verbose:
            print('Storing in ' + outputfile + '.root')
    elif file_type in ["h5", "hd5", "hdf5"]:
        service = I3HDFTableService(outputfile + '.hd5')
        if verbose:
            print('Storing in ' + outputfile + '.hd5')
    else:
        service = I3HDFTableService(outputfile + '.hd5')
        if verbose:
            print 'Using standard file_type: hd5.'
            print('Storing in ' + outputfile + '.hd5')

    if generateID:
        tray.AddModule(generic_attributes.create_event_id, 'HeaderModifier')

    # write chosen attributes
    tray.AddModule(I3TableWriter,'writer',
                   tableservice = [service],
                   BookEverything = True,
                   SubEventStreams = [sub_event_stream]
                  )

    # close file
    tray.AddModule('TrashCan','can')
    tray.Execute()
    tray.Finish()


if __name__ == "__main__":
    # parse given options
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-i", "--inputfile", dest="inputpath",
                      help="Inputpath to crawl for files or filename.")
    parser.add_option("-o", "--outputfile", dest="outputfile",
                      help="Outputfile")
    parser.add_option("-t", "--type", dest="file_type", default="hdf5",
                      help="Choose outputfile_type. Available hdf5 and root.")
    parser.add_option("-s", "--subeventstream", dest="sub_event_stream",
                      default="InIceSplit",
                      help="Set the name of the particles sub event name")
    parser.add_option("-I", "--ID", dest="generateID", default=False,
                      action="store_true",
                      help="Generate new p-frame-based ID.")
    parser.add_option("-v", "--verbose", dest="verbose",
                      default=True, action="store_true", 
                      help="Generate console output")
    (options, args) = parser.parse_args()

    # start conversion
    convert(options.inputpath,
            options.outputfile,
            options.file_type,
            options.sub_event_stream,
            options.verbose,
            options.generateID)
