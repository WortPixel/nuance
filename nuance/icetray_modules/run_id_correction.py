#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Icetray module providing functionality to generate correct I3Event
Headers. This module was used for some broken simulations.
This Module only works for uncutted files, because it determines the
current files via a decrese in the Event ID.'''
from __future__ import division, print_function

import os
import copy

from icecube import icetray, dataclasses


class run_id_corrector(icetray.I3ConditionalModule):
    '''IceTray Module roviding functionality to generate correct I3Event
       Headers. The module checks the Event IDS to track when the next
       File is read and adjustes the I3EventHeader.'''
    def __init__(self, context):
        '''Standard module __init__, two parameters are added:
            - "i3files" expecting the list of files same list as
                I3Reader
            - "report" False/True  wether to print control output in the
                Finish method'''
        icetray.I3ConditionalModule.__init__(self, context)
        self.AddParameter('i3_files',                 # name
                          'i3 files read in',       # doc
                          None)
        self.AddParameter('pos_dataset',                 # name
                          'Position of dataset in filename',  # doc
                          None) 
        self.AddParameter('pos_run',                 # name
                          'Position of filenumber/run in filename',  # doc
                          None)                            # default
        self.AddParameter('report',                 # name
                          'Report switching of IDs',       # doc
                          False)                           # default

    def Configure(self):
        '''The two parameters added in the __init__ method are fetched.
            and variables to count frames are initilized.'''
        i3_files = self.GetParameter('i3_files')
        self.pos_dataset = int(self.GetParameter('pos_dataset'))
        self.pos_run = int(self.GetParameter('pos_run'))
        if i3_files is not None:
            self.run_ids = self.extract_runids(i3_files)
            self.current_run = 0
        else:
            self.run_ids = range(len(i3_files))
            self.current_run = 0
        self.report = self.GetParameter('report')
        self.report_list = []
        self.q_frame_counter = 0
        self.p_frame_counter = 0
        self.new_event_id = 0  # used as new ongoing event id
        self.last_event_id = -1  # stores original event id of last frame

    def DAQ(self, frame):
        '''Count frame and adjust I3EventHeader.'''
        self.q_frame_counter += 1
        self.PushFrame(frame)

    def Physics(self, frame):
        '''Same as DAQ. Probably the correct_id is absolete because
        Q-Frames and P-Frames have the same event header.y.'''
        frame = self.correct_id(frame)
        self.p_frame_counter += 1
        self.PushFrame(frame)

    def Finish(self):
        '''Prepare the report and print when "report" was True.'''
        last_run_id = int(self.run_ids[self.current_run])
        self.report_list.append([last_run_id, self.q_frame_counter,
                                 self.p_frame_counter])
        if self.report:
            for run in self.report_list:
                print('%d Q-Frames and %d P-Frames with Run ID: %d' % (run[1],
                                                                       run[2],
                                                                       run[0]))

    def extract_runids(self, i3_files):
        '''Fucntion to extract the Run IDs (file numbers) from the
        in_path.'''
        run_ids = []
        for f in i3_files:
            file_name = os.path.basename(f)
            splitted_file_name = file_name.split('.')
            dataset = splitted_file_name[self.pos_dataset]
            file_nr = splitted_file_name[self.pos_run]
            run_ids.append((int(dataset)*10000) + int(file_nr)*10)
        return run_ids

    def correct_id(self, frame):
        '''Function that copys the old event header, adjusts the runID, eventID
        and adds the new header to the frame.'''
        header = copy.copy(frame['I3EventHeader'])
        del frame['I3EventHeader']
        current_event_id = header.event_id
        if current_event_id < self.last_event_id:
            last_run_id = int(self.run_ids[self.current_run])
            self.report_list.append([last_run_id, self.q_frame_counter,
                                     self.p_frame_counter])
            self.current_run += 1
            self.q_frame_counter = 0
            self.p_frame_counter = 0
        if self.current_run >= len(self.run_ids):
            new_run_id = self.run_ids[self.current_run - 1]
            new_run_id += 1
            self.run_ids.append(new_run_id)
        header.run_id = self.run_ids[self.current_run]
        self.new_event_id += 1
        header.event_id = self.new_event_id
        frame['I3EventHeader'] = header
        self.last_event_id = current_event_id
        return frame


class check_run_ids(icetray.I3ConditionalModule):
    '''Class to control the the I3EventHeader.'''
    def __init__(self, context):
        icetray.I3ConditionalModule.__init__(self, context)

    def Configure(self):
        self.id_dict = {}

    def DAQ(self, frame):
        try:
            self.id_dict[frame['I3EventHeader'].run_id][0] += 1
        except:
            self.id_dict[frame['I3EventHeader'].run_id] = [1, 0]

    def Physics(self, frame):
        try:
            self.id_dict[frame['I3EventHeader'].run_id][1] += 1
        except:
            self.id_dict[frame['I3EventHeader'].run_id] = [0, 1]

    def Finish(self):
        print('\nIn resulting File are:')
        for key in self.id_dict.keys():
            q_events, p_events = self.id_dict[key]
            print('%d Q-Frames and %d P-Frames with Run ID: %d' % (q_events,
                                                                   p_events,
                                                                   key))
