#!/usr/bin/env python

"""
author: mzoll <marcel.zoll@fysik.su.se>

script to read and process information in the plain-tabulated Goodrun-list in the new format:
format is #(RunNum/Good_i3/Good_it/LiveTime(s)/ActiveStrings/ActiveDoms/ActiveInIceDoms/OutDir/Comment(s))

use this like this
  g = good_run_list()
  g.add_good_run_list('http://convey.icecube.wisc.edu/data/exp/IceCube/2011/filtered/level2/IC86_2011_GoodRunInfo.txt')
  g.exclude_runs([1,2,3]) #remove some unwanted runs
  g.exclude_runs("/home/user/IC86-I_exclude.txt") #alternatively found in a tabulated file
  for i in g.runs(): #remove all runs which have no good in_ice
    if not g.get_run_info(i).inice_ok:
      g.pop(i)
"""

import os, sys, glob

class run_info():
  def __init__(self):
    self.run_id = -1
    self.livetime_sec = -1
    self.inice_ok = -1
    self.icetop_ok = -1
    self.active_strings = -1
    self.active_doms = -1
    self.active_inice = -1
    self.path = ''
    self.comment = ''
  def get_date(self):
    """ extract the date of this run from the folder it is present in """
    if (self.run_id!=-1 and self.path!=''):
      try:
        d = self.path.split("/")
        d.pop(0) #zeroth place is a supposibly "" in an absolute path
        if d[-1]=='':
          d.pop(-1)
        return (int(d[3]),int(d[6][:2]),int(d[6][2:])) #format (yyyy,mm,dd)                                                                   
      except:
        raise ValueError("unexpected path format")
    return (-1,-1,-1)

  def n_files(self):
    """ retrieve the number of Parts/Subruns this run produced, by peaking into the folder """
    if (self.run_id!=-1 and self.path!=''):
      try:
        files = glob.glob(os.path.join(self.path,"Level2_IC86.???_data_Run%08d_*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].i3.bz2"%(self.run_id)))
        n_files = len(files)
        return n_files
      except:
        pass
    return -1
  
  
class good_run_list():
  """ this is the object you want to operate on """
  def __init__(self):
    self.run_info_dict = {} #format (run_id: run_info)
    
  def add_good_run_list(self,filepath):
    """ add the info from a goodrun_list file """

    infile = open(filepath, 'r')
    lines = infile.readlines()
    #skip the first two lines
    for thisline in lines[2:]:
      thiswords = thisline.split(" ")
      thiswords = [v for v in thiswords if v not in ['','\n'] ]
      try:
        ri = run_info()
        ri.run_id = int(thiswords[0])
        ri.inice_ok = bool(thiswords[1])
        ri.icetop_ok = bool(thiswords[2])
        ri.livetime_sec = float(thiswords[3])
        ri.active_strings = int(thiswords[4])
        ri.active_doms = int(thiswords[5])
        ri.active_inice = int(thiswords[6])
        ri.path = thiswords[7]
        if (len(thiswords)>8):
          ri.comment = ' '.join(thiswords[8:])
        #now append it to the dict
        self.run_info_dict[ri.run_id] =ri
          
      except:
        print "Unexpected file format: !!!SKIP!!!: '%s' "%(str(thiswords))
        #raise ValueError("Unexpected file format")
    infile.close()
  
  def runs(self):
    return self.run_info_dict.keys()
  
  def exclude_runs(self, arg):
    """ remove a list of runs from the goodrun-list """
    if (isinstance(arg, list)):
      for r in arg:
        try:
          self.run_info_dict.pop(r)
        except:
          pass
    elif (isinstance(arg,str)):
      try:
        infile = open(filepath, 'r')
        lines = infile.readlines()
        for thisline in lines:
          thisword = thisline.strip('\n')
          r = int(thisword)
          self.run_info_dict.pop(r)
      except:
        pass
      
  def get_run_info(self,run_id):
    """ retrieve the info for a specific specific run """
    if run_id in self.run_info_dict.keys():
      return self.run_info_dict[run_id]
    else:
      print "%d not found in goodrunlist!" % (run_id)
      return run_info()
