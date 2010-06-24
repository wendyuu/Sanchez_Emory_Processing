#! /usr/bin/env python
# Change the measurement frame to (1,0,0) (0,1,0) (0,0,1) and origin to (0 0 0) space dir to dim1,0,0; 0,dim2,0; 0,0,dim3, space to LPS
# Yundi Shi

import os
import math
import fnmatch
import sys
import shutil
from optparse import OptionParser

orig_fname = sys.argv[1];
center_fname = sys.argv[2];
print 'Change the measurement frame of '+orig_fname+' to '+center_fname +'  with (1 0 0) (0 1 0) (0 0 -1),center it and reorient it (change the space dir)'

usage = "usage: %prog [options] arg"

parser = OptionParser(usage)
parser.add_option("-t", "--tensor", action="store_true", dest="TensorFile", default=False)
parser.add_option("-d", "--dwi", action="store_true", dest="DWIFile", default=False)
parser.add_option("-n", "--noCenter", action="store_true", dest="noCenter", default=False)
(options, args) = parser.parse_args()

# get the pixdim and use it to determine the space direction
# reorient tensor and FA files to make the image align with the world coordinate system
origPixdim = os.popen('ImageStat '+orig_fname+' -info | grep Pixdims').read()
origPixdims = str(origPixdim).split(' ');
if(options.TensorFile):
    space_dir_line = 'space directions: none ('+origPixdims[1]+',0,0) '+'(0,'+origPixdims[2]+',0) '+'(0,0,'+origPixdims[3].replace('\n','')+')\n'
elif(options.DWIFile == False):
    space_dir_line = 'space directions: ('+origPixdims[1]+',0,0) '+'(0,'+origPixdims[2]+',0) '+'(0,0,'+origPixdims[3].replace('\n','')+')\n'

f_orig = open(orig_fname,'r')

content = '';
for line in f_orig.readlines():
    if(fnmatch.fnmatch(line,'measurement frame:*') and options.DWIFile== True):
        print 'Replacing '+line+' with measurement frame: (1,0,0) (0,1,0) (0,0,-1)\n'
        content = content + 'measurement frame: (1,0,0) (0,1,0) (0,0,-1)\n'
#         #extracting space direction list
#         grad3 = line.split(')')[2]
#         print grad3
#         grad3_list = grad3.split(',')
#         grad3_y = str(-1*float(grad3_list[1]));
#         print grad3_y
#         grad3_z = str(-1*float(grad3_list[2]));
#         print grad3_z
#         grad3_x = str(-1*float(grad3_list[0].split('(')[1]))
#         print grad3_x
#         newline = line.replace(grad3,' ('+grad3_x+','+grad3_y+','+grad3_z)
#         print 'Replacing '+line+' with '+newline
#         content = content + newline

    # reorient the image and change the space direction    
    elif (fnmatch.fnmatch(line,'measurement frame:*') and options.DWIFile==False):
        print 'Replacing '+line+' with measurement frame: (1,0,0) (0,1,0) (0,0,1)\n'
        content = content + 'measurement frame: (1,0,0) (0,1,0) (0,0,1)\n'
    # do not center    
    elif(fnmatch.fnmatch(line,'space origin*') and options.noCenter == False):
        print 'Replacing '+line+' with space origin: (0,0,0)\n'
        content = content + 'space origin: (0,0,0)\n'
    # reorient the image and change the space direction
    elif(fnmatch.fnmatch(line,'space directions:*')  and options.DWIFile==False):
        print 'Replacing '+line+' with '+ space_dir_line
        content = content + space_dir_line
    else:
        content = content + line;
f_orig.close();
f_center = open(center_fname,'w')
f_center.write(content)
f_center.close()

