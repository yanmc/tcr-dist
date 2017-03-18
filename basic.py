## LAZY-- some basic imports and shared params
##
##
from glob import glob
from os import popen, system, chdir, remove, getcwd
from os.path import exists, isdir, isfile
import math
from math import floor,sqrt
from sys import stderr,argv,exit
import random
from blargs import Parser
from parse_tsv import *

############################################################################################
############################################################################################
## some shared TCRdist analysis pipeline parameters

pipeline_params= {
    ## Use the update to probability calculation? (March 2017)
    'new_probs':True,

    ## A length-scale factor that lets us fiddle with the distance calculation
    ## and still get similar clustering and TCRdiv calculations
    ## The history is that with the original TCRdist we used nice round values of 25/50 for
    ## several distance thresholds. When we moved to the updated TCRdist, on average
    ## distances decreased by a factor of 1.355, so as a temporary hack we introduced
    ## this parameter so that clustering and diversity calculations can be run with
    ## default parameters and give similar results.
    'distance_threshold_25': 25.0 / 1.355,
}


## naming scheme for the gene segment types, occasionally useful for iterating
segtypes_uppercase = ['VA','JA','VB','JB']
segtypes_lowercase = ['va','ja','vb','jb']


############################################################################################
############################################################################################

def Log(s): ## silly legacy helper function
    stderr.write(s)
    if s and not s.endswith('\n'):
        stderr.write('\n')


## you could modify this function if you have a different cmdline tool for converting svg to png
## like inkscape or cairosvg
##
def convert_svg_to_png( svgfile, pngfile, verbose=True, allow_missing=False, allow_failure=True ):
    if not isfile(svgfile):
        errmsg = 'convert_svg_to_png: svgfile does not exist: {}'.format(svgfile)
        print errmsg
        Log( errmsg )
        if allow_missing:
            return
        else:
            exit()
    cmd = 'convert {} {}'.format( svgfile, pngfile )
    if verbose:
        print cmd
    system(cmd)
    if not isfile( pngfile ):
        ## this might also occur if the svgfile were empty...
        errmsg = 'convert command failed: cmd="{}" -- is the "convert" cmdline tool (Imagemagick) installed?'\
                 .format( cmd )
        print errmsg
        Log( errmsg )
        if not allow_failure:
            exit()

def get_mean_and_sdev( l ):
    N = len(l)
    assert N>0
    mean = float( sum( l ) ) / N
    sdev = 0.0
    for x in l: sdev += ( x- mean )**2

    sdev = sqrt( float(sdev)/N )
    return mean, sdev

def get_median(l_in):
    l = l_in[:] ##make copy
    l.sort()
    n = len(l)
    if n%2: return l[n/2]  ## n is odd
    else: return 0.5 * ( l[n/2] + l[n/2 - 1 ] ) ## n is even

