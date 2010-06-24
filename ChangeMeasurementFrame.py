#! /usr/bin/env python
# Change the measurement frame to (1,0,0) (0,1,0) (0,0,1) and origin to (0 0 0)
# Yundi Shi


import os
import math
import fnmatch
import sys
import shutil


orig_fname = sys.argv[1];
center_fname = sys.argv[2];
print 'Change the measurement frame of '+orig_fname+' to '+center_fname +'  with (1 0 0) (0 1 0) (0 0 1)  and center it'

f_center = open(center_fname,'w')
f_orig = open(orig_fname,'r')
content = '';
for line in f_orig.readlines():
    if(fnmatch.fnmatch(line,'measurement frame*')):
        print 'Replacing '+line+' with measurement frame: (1,0,0) (0,1,0) (0,0,1)\n'
        content = content + 'measurement frame: (1,0,0) (0,1,0) (0,0,1)\n'
    elif(fnmatch.fnmatch(line,'space origin*')):
        print 'Replacing '+line+' with space origin: (0,0,0)\n'
        content = content + 'space origin: (0,0,0)\n'                
    else:
        content = content + line;
f_orig.close();
f_center.write(content)
f_center.close()
           


                                                             
                                   

                                                        
