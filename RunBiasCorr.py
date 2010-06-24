#! /usr/bin/env python
# Run bias correction in the atlas orig_img folder

# Yundi Shi

import os
import math
import fnmatch
import sys
import shutil
from optparse import OptionParser

parser = OptionParser()
(options, args) = parser.parse_args()

if (len(args) == 1):
    age = sys.argv[1];
else:
    print 'Usage: RunBiasCorr.py [age]'
    sys.exit('Look at the usage and try it again')

from string import Template
TCorrectBiasDWICmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/CorrectBiasDWI.py $infile $outfile')

ORIG_DIR = os.path.join('/primate/SanchezEmory/BrainDevYerkes/DTIAtlas_Upsampled/',age,'origImage')
CORR_DIR = os.path.join('/primate/SanchezEmory/BrainDevYerkes/DTIAtlas_Upsampled/',age,'biasCorrImage')

if (os.path.exists(CORR_DIR)==False): os.mkdir(CORR_DIR)

#Loop through all the dwis
for img in fnmatch.filter(os.listdir(ORIG_DIR),'R??13_'+age+'_30dir_10DWI_*addB0_upsampled_center.nrrd'):
    Subj = img[0:5];
    Subj_DIR = os.path.join('/primate/SanchezEmory/BrainDevYerkes',Subj,age,'DTI');
    ORIG_DWI = os.path.join(ORIG_DIR,img)
    CORR_DWI = ORIG_DWI.replace('.nrrd','_CorrBias.nrrd').replace(ORIG_DIR,CORR_DIR)
    BiasCorrectlog = os.path.join(CORR_DIR,Subj+'_BiascorrectLog.log')
    BrainMask = os.path.join(Subj_DIR,fnmatch.filter(os.listdir(Subj_DIR),'*brainMask_T2Areg*')[0])
    if (os.path.exists(CORR_DWI)==False):
        CorrectBiasDWICmd = TCorrectBiasDWICmd.substitute(infile=ORIG_DWI,outfile=CORR_DWI,BM=BrainMask)
        print '*********************************************************************************************************************************************************'
        print CorrectBiasDWICmd.replace(' ','\n')
        print '*********************************************************************************************************************************************************'
        os.system(CorrectBiasDWICmd+' 2>&1 |tee '+BiasCorrectlog)

                         
