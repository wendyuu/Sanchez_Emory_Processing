#! /usr/bin/env python

# Script to unzip the 6months data including T1, 6mmT1 and T2 and converting them to nrrd
import os
import fnmatch
import sys
from optparse import OptionParser

ORIG_DIR = '/primate/SanchezEmory/BrainDevYerkes/'

# prefix of the file names
# either read it from a file or as input
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename",
                  help="read data from FILE", metavar="FILE")
parser.add_option("-r","--redo", action="store_true", dest="redo", default=False)


(options, args) = parser.parse_args()
dir_tag = args[0];
print dir_tag
if options.filename:
   print 'Reading input from file '+options.filename
   prefixfile = os.path.join(ORIG_DIR,'processing',options.filename);
   prefixlist = open(prefixfile,'r');
else:
   print ('Input error: Either give a file name to read the prefix names of the subjects')


for line in prefixlist:
   print 'Now Processing Subject ' + line;
   prefix = line[0:5];
   curr_loc =  os.path.join(ORIG_DIR,prefix,dir_tag,'DTI');
   print curr_loc
   for DWIname in fnmatch.filter(os.listdir(curr_loc),prefix+'_'+dir_tag+'_30dir_??DWI_*addB0.nrrd'):
      print DWIname
      DWIname = os.path.join(curr_loc,DWIname);
      
      FAname = DWIname.replace(prefix+'_','FA_'+prefix+'_');
      cFAname = FAname.replace('FA','cFA');
      MDname = FAname.replace('FA','MD');
      iDWIname = FAname.replace('FA','iDWI');
      
      Tensorname = FAname.replace('FA','TENSOR');
      print Tensorname
      Lambda1 = FAname.replace('FA','Lambda1');
      Lambda2 = FAname.replace('FA','Lambda2');
      Lambda3 = FAname.replace('FA','Lambda3')

      # run dtiestim
      if(os.path.exists(Tensorname)==False or options.redo == True):
         cmd = 'dtiestim '+DWIname+' '+Tensorname+' -m wls -t 20 --idwi '+iDWIname
         print cmd
         os.system(cmd);
   
      # run dtiprocess
      cmd = 'dtiprocess '+Tensorname+' -f '+FAname+' -m '+MDname+' -c '+cFAname+' --lambda1-output '+Lambda1+' --lambda2-output '+Lambda2+' --lambda3-output '+Lambda3 + ' --scalar-float'
      print cmd
      os.system(cmd);
          
