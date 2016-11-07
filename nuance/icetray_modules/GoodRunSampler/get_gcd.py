#!/usr/bin/python
import os, sys, glob
from get_runlist import getRuns

def getGCD(run = 0):
    grl_file = None

    scriptpath = os.path.realpath(__file__)    

    burnrate = 1
    if run%100 == 0:
        burnrate = 100
    if run%10 == 0:
        burnrate = 100

    # Try IC86-1
    grl_file = getRuns("2011", burnrate, False)
    if run in grl_file.keys():
        return grl_file[run][0][0]
    
    # Try IC86-2
    grl_file = getRuns("2012", burnrate, False)
    if run in grl_file.keys():
        return grl_file[run][0][0]
    
    # Try IC86-3
    grl_file = getRuns("2013", burnrate, False)
    if run in grl_file.keys():
        return grl_file[run][0][0]

    # Try IC86-3
    grl_file = getRuns("2014", burnrate, False)
    if run in grl_file.keys():
        return grl_file[run][0][0]

    print "Run doesn't show up in IC86-1-4!"
