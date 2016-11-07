#!/usr/bin/python
import os, sys, glob
from goodrunlist import good_run_list
from get_runlist import *

def getTime(runs = [], season="2011", messages=False):
    grl_file = None

    scriptpath = os.path.dirname(os.path.realpath(__file__))

    if season == "2011": # IC86-1
        grl_file = os.path.join(scriptpath, "IC86_2011_GoodRunInfo.txt")
    elif season == "2012": # IC86-2
        grl_file = os.path.join(scriptpath, "IC86_2012_GoodRunInfo.txt")
    elif season == "2013": # IC86-3
        grl_file = os.path.join(scriptpath, "IC86_2013_GoodRunInfo.txt")
    elif season == "2014": # IC86-4
        grl_file = os.path.join(scriptpath, "IC86_2014_GoodRunInfo.txt")

    # Open the relevent GRL file
    g = good_run_list()
    g.add_good_run_list(grl_file)
    
    # good runs only!
    good_inice = {}
    good_livetime = 0
    for run in runs:
        info = g.get_run_info(run)

        # Finally, add the livetime
        good_livetime += info.livetime_sec

    return good_livetime


if __name__ == "__main__":
    print "2011: ", getTime(getRuns("2011",1, False, False).keys(), "2011")
    print "2012: ", getTime(getRuns("2012",1, False, False).keys(), "2012")
    print "2013: ", getTime(getRuns("2013",1, False, False).keys(), "2013")
    print "2014: ", getTime(getRuns("2014",1, False, False).keys(), "2014")
