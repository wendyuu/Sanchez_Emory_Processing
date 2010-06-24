#! /usr/bin/env python
# Change the format of the data to float

import os
import math
import fnmatch
import sys

ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
from string import Template
TunucvtCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu convert -i $infile -t float | /tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -o $outfile -e gzip -f nrrd');
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -i $infile -o $infile -e gzip -f nrrd');

for dir_tag in ['2weeks','3months','6months']:
    print ('Now Processing the atlas of ' + dir_tag)      
    Orig_loc = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled',dir_tag,'origImage');
    Float_loc = os.path.join('/primate/Emory_data_forGabe/orig_dti/',dir_tag);
    for tensor in fnmatch.filter(os.listdir(Orig_loc),'TENSOR_*.nrrd'):
        DTI = os.path.join(Orig_loc,tensor)
        DTI_float = DTI.replace('.nrrd','_float.nrrd').replace(Orig_loc,Float_loc)
        if (os.path.exists(DTI_float)==False):
            cvtCmd = TunucvtCmd.substitute(infile=DTI,outfile=DTI_float)
            print cvtCmd
            os.system(cvtCmd)
        
                
        
                                                        

