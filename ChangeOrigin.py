#! /usr/bin/env python
# Change the origin to 0,0,0
# Yundi Shi


import os
import math
import fnmatch
import sys
import shutil

print 'Usage: ChangeOrigin.py orig_name center_name'

orig_fname = sys.argv[1];
center_fname = sys.argv[2];
print 'Center Image '+orig_fname+' to '+center_fname

f_orig = open(orig_fname,'r')
content = '';
for line in f_orig.readlines():
    if(fnmatch.fnmatch(line,'space origin*')):
        print 'Replacing '+line+' with space origin: (0,0,0)\n'
        content = content + 'space origin: (0,0,0)\n'
    else:
        content = content + line;
f_orig.close()
f_center = open(center_fname,'w')
f_center.write(content)
f_center.close()
           


                                                             
                                   

                                                        
