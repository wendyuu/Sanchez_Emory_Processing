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

(options, args) = parser.parse_args()

if options.filename:
   print 'Reading input from file '+options.filename
   prefixfile = os.path.join(ORIG_DIR,'processing',options.filename);
   prefixlist = open(prefixfile,'r');
elif len(args) > 0:
   print 'Reading input from the terminal'
   prefixlist = args;
else:
   print ('Input error: Either give a file name to read the prefix names of the subjects or type in from the terminal')


for line in prefixlist:
    print 'Now Processing Subject ' + line;
    prefix = line[0:5];
   
    for suffix in ['_T1_6months','_T1_666_6months','_T2_6months']:
	zipname = os.path.join(ORIG_DIR,'orig',prefix+suffix);
	# unzip the data
	print 'Now Processing Subject ' + prefix + suffix;
	if (os.path.exists(zipname) == False):
	   os.system('unzip ' + zipname + '.zip -d ' + zipname);
	else:
	   if (os.path.exists(zipname+'.zip') == False): os.system('tar -cf '+zipname+'.zip '+zipname+'/*')
	   print 'Already unzipped'
	
	# mkdir the sMRI folder
	curr_loc =  os.path.join(ORIG_DIR,prefix)
	if(os.path.exists(curr_loc)==False): os.system('mkdir ' + curr_loc);
	curr_loc =  os.path.join(curr_loc,'6months');
	if(os.path.exists(curr_loc)==False): os.system('mkdir ' + curr_loc);
	curr_loc =  os.path.join(curr_loc,'sMRI');
	if(os.path.exists(curr_loc)==False): os.system('mkdir ' + curr_loc);
	print curr_loc
	
	# convert T1_06mm
	if suffix.lower().find('666'.lower()) >= 0:
	   T1name = os.path.join(curr_loc,prefix  + '_6months_T1_060606mm.nhdr');
	   print 'DicomConverting ' + zipname + ' to ' + T1name;
	   os.system('DicomConvert ' + os.path.join(zipname,'*/') + ' ' + T1name +' -v');
	   os.system('rm -rf ' + zipname);
	# convert T1_05mm
	elif suffix.lower().find('t2'.lower()) >= 0:
	    T2name = os.path.join(curr_loc,prefix  + '_6months_T2_050510mm.nhdr');
	    print 'DicomConverting ' + zipname + ' to ' + T2name;
	    os.system('DicomConvert ' + os.path.join(zipname,'*/') + ' ' + T2name +' -v');
	    os.system('rm -rf ' + zipname);
	elif suffix.lower().find('t1'.lower()) >= 0:
	    T1name = os.path.join(curr_loc,prefix  + '_6months_T1_050505mm.nhdr');
	    print 'DicomConverting ' + zipname + ' to ' + T1name;
	    os.system('DicomConvert ' + os.path.join(zipname,'*/') + ' ' + T1name +' -v');
            os.system('rm -rf ' + zipname);
		
			



