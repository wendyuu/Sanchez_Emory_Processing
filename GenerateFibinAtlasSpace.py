#! /usr/bin/env python
# Center the images for slicer3
# Generate fib files
# Yundi Shi

print 'Usage:\n\
GenerateFibinAtlasSpace.py age'

import os
import math
import fnmatch
import sys

##########Parameters used for atlas building regarding subject selection##########
age = sys.argv[1];
################################################################################## 

from string import Template
Tunu2nhdrCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -i $infile -o $outfile');
TCopyHdrCmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/CopyHdr.py $Atlas $orig $tar');
TFiberProcCmd = Template('/tools/bin_linux64/fiberprocess $infiber -o $outfiber -T $dti')

ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
ATLAS_DIR = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled',age,'normFA/Areg2template/all_subjects/DTIAtlas')
FIB_DIR = os.path.join(ATLAS_DIR,'fiber')
if (os.path.exists(FIB_DIR)==False):
    os.mkdir(FIB_DIR)
DTIATLAS = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled',age,'normFA/Areg2template/all_subjects/DTIAtlas','DTIAtlas_'+age+'_w_allsubjectsAreg2templateUsingnormFAWithdtiproc_float_centered4slicer3.nhdr');
FIBATLAS = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled',age,'normFA/Areg2template/all_subjects/DTIAtlas',age+'_splenium_aftercleaning.fib')
IND_DIR = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled',age,'normFA/Areg2template/all_subjects/WarpedDTI');

for file in os.listdir(IND_DIR):
    if (fnmatch.fnmatch(file,'TENSOR*_upsampled_center_Warped_UsingnormFA_dtiproc.n???')):
        sub = file[7:12];
        ind_file = os.path.join(IND_DIR,file)
        # change file to nhdr format
        if os.path.exists(ind_file.replace('.nrrd','.nhdr')) == False:
            unu2nhdrCmd = Tunu2nhdrCmd.substitute(infile = ind_file,outfile = ind_file.replace('.nrrd','.nhdr'));
            print unu2nhdrCmd
            os.system(unu2nhdrCmd)
#            os.remove(ind_file)
        # center file
        ind_file = ind_file.replace('.nrrd','.nhdr')
        dti4slicer = ind_file.replace('.nhdr','_centered4slicer3.nhdr')
        if os.path.exists(dti4slicer) == False:
            CopyHdrCmd  = TCopyHdrCmd.substitute(Atlas = DTIATLAS,orig = ind_file.replace('.nrrd','.nhdr'),tar = dti4slicer)
            print CopyHdrCmd
            os.system(CopyHdrCmd)
        # generate fib file
        fib = FIBATLAS.replace('.fib','_'+sub+'.fib').replace('ATLAS_DIR','FIB_DIR')
        if os.path.exists(fib) == False:
            FiberProcCmd = TFiberProcCmd.substitute(infiber=FIBATLAS,outfiber=fib,dti=dti4slicer)
            print FiberProcCmd
            os.system(FiberProcCmd)
            

