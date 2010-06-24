#! /usr/bin/env python
# simple thresholding FA to generate WM masks

import os
import math
import fnmatch
import sys

ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
from string import Template
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -threshold $thre,1.0 -outfile $outfile');


for dir_tag in ['2weeks','3months','6months']:
    print ('Now Processing the atlas of ' + dir_tag)
    FA_loc = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled',dir_tag,'origImage');
    WM_loc = os.path.join('/primate/Emory_data_forGabe/orig_dti/',dir_tag);
    for faname in fnmatch.filter(os.listdir(FA_loc),'FA_*.nrrd'):
        FA = os.path.join(FA_loc,faname)
        WMmask = FA.replace('FA_','WMMask_').replace(FA_loc,WM_loc)
        ImageMathCmd = TImageMathCmd.substitute(infile=FA,outfile=WMmask,thre='0.25')
        print ImageMathCmd
        os.system(ImageMathCmd)
        
                
        
                                                        

