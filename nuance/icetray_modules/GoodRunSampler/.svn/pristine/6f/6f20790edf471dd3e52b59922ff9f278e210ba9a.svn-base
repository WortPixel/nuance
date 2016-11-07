#!/usr/bin/python
import os, sys, glob
from goodrunlist import good_run_list


def getRuns(season = "2011", burnrate = 100, printComments = True, printLivetime = False):
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
    for run in g.runs():
        info = g.get_run_info(run)
        if not info.inice_ok: continue                # Need good in ice
        if info.active_strings < 86: continue    # Full detector only
        if info.active_inice < 5030: continue    # Full detector only
        if info.livetime_sec < 7*60*60: continue  # 7 hours and above only
        if info.livetime_sec > 9*60*60: continue  # 9 hours and below only

        if info.comment and printComments:
            print run, info.comment[:-1]
   
        # Burn it
        if not run % burnrate == 0: continue
        
        # Run seems okay. Add it
        # Get the list of files in the directory path
        filelist = glob.glob( os.path.join( info.path, "Level2_IC86*Run%08i*[0-9].i3.bz2" % run) )
        filelist.sort()

        # One of those is the GCD
        gcd = glob.glob( os.path.join( info.path, "Level2_IC86*Run%08i*GCD.i3.gz" % run) )
        good_inice[run] = [gcd, filelist]

        # Finally, add the livetime
        good_livetime += info.livetime_sec

    if printLivetime:
        print "Found %i runs with a total livetime of %f" % (len(good_inice.keys()), good_livetime)
    return good_inice

    
if __name__ == "__main__":
    print "2011: ", getRuns("2011",100, False, True).keys()
    print "2012: ", getRuns("2012",100, False, True).keys()
    print "2013: ", getRuns("2013",100, False, True).keys()
    print "2014: ", getRuns("2014",100, False, True).keys()
