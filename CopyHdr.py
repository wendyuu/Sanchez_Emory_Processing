#! /usr/bin/env python
# Copy header of the atlas to individual file
# Yundi Shi

print 'Usage:\n\
CopyHdr.py Atlas IndFile CopyFile'

import os
import math
import fnmatch
import sys

Atlas = open(sys.argv[1],'r')

for line in Atlas:
    if fnmatch.fnmatch(line,'space:*'):
            spaceline = line
    elif fnmatch.fnmatch(line,'space directions:*'):
        spacedir = line
    elif fnmatch.fnmatch(line,'space origin:*'):
        spaceorig = line
        
IndFile = open(sys.argv[2],'r')
hdr = '';
for line in IndFile:
    if fnmatch.fnmatch(line,'space:*'):
            hdr = hdr + spaceline
    elif fnmatch.fnmatch(line,'space directions:*'):
        hdr = hdr + spacedir
    elif fnmatch.fnmatch(line,'space origin:*'):
        hdr = hdr + spaceorig
    else:
        hdr = hdr + line
    
CopyFile = sys.argv[3]

#print hdr
f = open(CopyFile,'w')
f.write(hdr)

