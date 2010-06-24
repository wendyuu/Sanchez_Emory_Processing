#! /usr/bin/env python
# Check the imagespacedir and measurement frame
#
# Yundi Shi

print 'Usage:\n\
CheckImageSpaceDir.py \n\
[\'file_fearure\' (e.g. R??13_?_30dir_10DWI_*.nrrd)]'

import os
import math
import fnmatch
import sys
from optparse import OptionParser

Orig_Dir = '/primate/SanchezEmory/BrainDevYerkes/'
unuhead = '/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu head '

if(sys.argv[1] == 'TENSOR'):
    feature = 'TENSOR';
    logname = os.path.join(Orig_Dir,'CheckImgSpaceDir_TENSOR_log.txt');
elif(sys.argv[1] == 'FA'):
    feature = 'FA';
    logname = os.path.join(Orig_Dir,'CheckImgSpaceDir_FA_log.txt');
else:
    feature = 'R??13'
    
for line in sys.argv[2:]:
    feature = feature + '*'+line;
    logname = os.path.join(Orig_Dir,'CheckImgSpaceDir_TENSOR_log.txt');
feature = feature + '*'

log_content = '';
f = open(logname,'w');
#feature of the file we'll be looking at


print feature
print Orig_Dir

for age in ['2weeks','3months','6months']:
    print '*******************'+age+'*******************'
    log_content = log_content + '*******************'+age +'*******************'+'\n'
    for subject_folder in os.listdir(Orig_Dir):
        if(fnmatch.fnmatch(subject_folder,'R??13')):
           #subject folder
           DTI_Dir = os.path.join(Orig_Dir,subject_folder,age,'DTI');
           if os.path.exists(DTI_Dir):
               for file in os.listdir(DTI_Dir):
                   if fnmatch.fnmatch(file,feature):
                       print file
                       log_content = log_content + file + '\n'
                       
                       nhdrContent = os.popen(unuhead+os.path.join(DTI_Dir,file)).read();

                       spacedir_line = fnmatch.filter(nhdrContent.split('\n'),'space directions:*')[0];
                       print spacedir_line
                       log_content = log_content + '  '+ spacedir_line + '\n' + '\n'
                       
                       spacedir_line = fnmatch.filter(nhdrContent.split('\n'),'measurement frame*')[0];
                       print spacedir_line
                       log_content = log_content + '  '+ spacedir_line + '\n' +'\n'
                       
f.write(log_content)
f.close()
                   
                   
                   
               
               
           
       
       
       
