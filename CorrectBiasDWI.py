#! /usr/bin/env python
# Use N3 in freesurfer for bias field correction for bias field correction 
# Use nu_estimate to estimate the bias field of B0
# Use nu_evaluate to apply the bias field to the dwi

# Yundi Shi

import os
import math
import fnmatch
import sys
import shutil
from optparse import OptionParser

usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-m", "--mask", dest="brainmask",help="Brain Mask")

(options, args) = parser.parse_args()


if (len(args) == 2):
    orig_DWI= sys.argv[1];
    corr_DWI = sys.argv[2];
else:
    print 'Usage: CorrectBiasDWI.py [inputvol] [outputvol] --mask[-m] [Brain Mask Vol]'
    sys.exit('Look at the usage and try it again')

from string import Template
# change the format back and forth from .mnc
TChangeMNCCmd = Template('/opt/local/Freesurfer_4_64/bin/mri_convert $infile $outfile')
#TChangeMNCCmd = Template('/opt/local/Freesurfer_4_64/bin/mri_nu_correct.mni --i $infile --o $outfile --n 0')
if (options.brainmask):
    TNuEstimateCmd = Template('/opt/local/Freesurfer_4_64/mni/bin/nu_estimate $infile $map -clobber -mask $BM')
else:
    TNuEstimateCmd = Template('/opt/local/Freesurfer_4_64/mni/bin/nu_estimate $infile $map -clobber')
TNuEvaluateCmd = Template('/opt/local/Freesurfer_4_64/mni/bin/nu_evaluate $infile $outfile -mapping $mapping -clobber')
TunusaveCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -i $infile -o $outfile -e gzip')
TunugunzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -i $infile -o $infile -e raw')
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -i $infile -o $infile -e gzip')
TunudiceCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu dice -a 3 -i $infile -o $output_prefix')
TunuscaleCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu 2op x $infile 25 -o $outfile')
TcvtCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
# join nrrd along the 4th dimension
unujoinCmd = '/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu join -a 3 -i'
unuheadCmd = '/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu head '
# log_cmd = ''
#1. Generate B0
B0 = orig_DWI.replace('.nrrd','_mnitemp_B0.nrrd');
DTI = orig_DWI.replace('.nrrd','_mnitemp_tensor.nrrd');
dtiestim_cmd = 'dtiestim '+orig_DWI+' '+DTI+' -t 20 --B0 '+B0
# log_cmd = # log_cmd + dtiestim_cmd + '\n '
os.system(dtiestim_cmd)
os.remove(DTI)
#convert b0 to nii
B0_nii = B0.replace('.nrrd','.nii')
cvtCmd = TcvtCmd.substitute(infile=B0,outfile=B0_nii)
# log_cmd = # log_cmd +  cvtCmd  + '\n '
os.system(cvtCmd)
os.remove(B0)

#2. Change B0 to .mnc
B0_mnc = B0.replace('.nrrd','.mnc')
ChangeMNCCmd = TChangeMNCCmd.substitute(infile=B0_nii,outfile=B0_mnc)
# log_cmd = # log_cmd +  ChangeMNCCmd  + '\n '
os.system(ChangeMNCCmd)
os.remove(B0_nii)

BM_mnc = ''
#3. Generate brain mask
if (options.brainmask):
    BM = options.brainmask;
    if (fnmatch.fnmatch(BM,'*.nii')==False):
        if len(BM.split('.'))==3:
            surfix = BM.split('.')[1]+'.'+BM.split('.')[2];
            print 'surfix is '+surfix
        else:
            surfix = BM.split('.')[1]
        #change to nii format
        BM_readin = BM;
        BM_nii = BM.replace(surfix,'nii')
        cvtCmd = TcvtCmd.substitute(infile=BM_readin,outfile=BM_nii)
        print cvtCmd
        os.system(cvtCmd)
    else:
        BM_nii = BM;
    BM_mnc = BM_nii.replace('.nii','.mnc')
    ChangeMNCCmd = TChangeMNCCmd.substitute(infile=BM_nii,outfile=BM_mnc)
    os.system(ChangeMNCCmd)
    os.remove(BM_nii)

#4. Estimate the correction field using nu_estimate
CorrMap = corr_DWI.replace('.nrrd','_Map.imp')
NuEstimateCmd = TNuEstimateCmd.substitute(infile=B0_mnc,map=CorrMap,BM=BM_mnc)
os.system(NuEstimateCmd)
if (options.brainmask):
    os.remove(BM_mnc)

#5. Split up the DWI into [number_of_gradient_direction] volumes
unudiceCmd = TunudiceCmd.substitute(infile = orig_DWI, output_prefix = os.path.join(os.path.dirname(orig_DWI),'mnitemp_diced_dwi'))
os.system(unudiceCmd)
# Get the size of the DWI and look through them one by one... has to be done this way because the gradient directions are not changed
nhdrContent = os.popen(unuheadCmd+orig_DWI).read()
text_str_size = fnmatch.filter(nhdrContent.split('\n'),'sizes:*')[0];
grad_num = int(text_str_size.split(' ')[4])

#5. Apply the correction field to all the volumes
orig_DWI_dir = os.path.dirname(orig_DWI);
for grad_id in range(grad_num):
    file = 'mnitemp_diced_dwi'+"%03d"%grad_id+'.nrrd';
    dwi_vol = os.path.join(orig_DWI_dir,file)
    dwi_mnc = dwi_vol.replace('.nrrd','.mnc')
    dwi_nii = dwi_vol.replace('.nrrd','.nii')
    dwi_corr = dwi_mnc.replace('.mnc','_corr.mnc')
    dwi_corr_nrrd = dwi_corr.replace('.mnc','.nrrd')
    dwi_corr_nii = dwi_corr.replace('.mnc','.nii')
    if(os.path.exists(dwi_corr_nrrd)==False):
        #change to nii format
        cvtCmd = TcvtCmd.substitute(infile=dwi_vol,outfile=dwi_nii)
        # log_cmd = # log_cmd +  cvtCmd  + '\n '
        os.system(cvtCmd)
        os.remove(dwi_vol)
        #change to mnc format
        ChangeMNCCmd = TChangeMNCCmd.substitute(infile=dwi_nii,outfile=dwi_mnc)
        # log_cmd = # log_cmd +  ChangeMNCCmd  + '\n '
        os.system(ChangeMNCCmd)
        os.remove(dwi_nii)
        #apply the correction field
        NuEvaluateCmd = TNuEvaluateCmd.substitute(infile=dwi_mnc,outfile=dwi_corr,mapping=CorrMap)
        # log_cmd = # log_cmd +  NuEvaluateCmd  + '\n '
        os.system(NuEvaluateCmd)
        #change to nrrd format
        ChangeMNCCmd = TChangeMNCCmd.substitute(infile=dwi_corr,outfile=dwi_corr_nii)
        # log_cmd = # log_cmd +  ChangeMNCCmd + '\n '
        os.system(ChangeMNCCmd)
        os.remove(dwi_corr)
        cvtCmd = TcvtCmd.substitute(infile=dwi_corr_nii,outfile=dwi_corr_nrrd)
        # log_cmd = # log_cmd +  cvtCmd  + '\n '
        os.system(cvtCmd)
        os.remove(dwi_corr_nii)
    #use unu join to generate raw file
    else:
        os.remove(dwi_vol)
    unujoinCmd = unujoinCmd + ' ' + dwi_corr_nrrd

#6. Merge them to one file
corr_DWI_nhdr = corr_DWI.replace('.nrrd','.nhdr')
unujoinCmd = unujoinCmd + ' -o ' + corr_DWI_nhdr
# log_cmd = # log_cmd +  unujoinCmd + '\n '
print unujoinCmd
os.system(unujoinCmd)

#7. Generate the correct header file
orig_DWI_nhdr = orig_DWI.replace('.nrrd','.nhdr');
unusaveCmd = TunusaveCmd.substitute(infile=orig_DWI,outfile=orig_DWI_nhdr)
print unusaveCmd
# # log_cmd= # # log_cmd+  unusaveCmd + '\n '
os.system(unusaveCmd)
os.remove(orig_DWI_nhdr.replace('.nhdr','.raw.gz'))
# copy over the original DWI header
f_orig = open(orig_DWI_nhdr,'r')

# change the content in the header
nhdr_content = ''
for line in f_orig.readlines():
    if fnmatch.fnmatch(line,'data file*'):
        newline = line.replace(os.path.basename(orig_DWI_nhdr.replace('.nhdr','.raw.gz')),os.path.basename(corr_DWI_nhdr.replace('.nhdr','.raw')))
        newline = newline.replace('.raw.gz','.raw')
        nhdr_content = nhdr_content + newline
    elif fnmatch.fnmatch(line,'data file*'):
        newline = line.replace(os.path.basename(orig_DWI_nhdr.replace('.nhdr','.raw.gz')),os.path.basename(corr_DWI_nhdr.replace('.nhdr','.raw')))
        newline = newline.replace('.raw.gz','.raw')
        nhdr_content = nhdr_content + newline
    else:
        nhdr_content = nhdr_content + line;
print nhdr_content
f_orig.close()        
f_corr = open(corr_DWI_nhdr,'w');
f_corr.write(nhdr_content);
f_corr.close();

# scale if up 25 times
#unuscaleCmd = TunuscaleCmd.substitute(infile=corr_DWI_nhdr,outfile=corr_DWI_nhdr)
#print unuscaleCmd
#os.system(unuscaleCmd)

# gzip and change it to nrrd
unusaveCmd = TunusaveCmd.substitute(infile=corr_DWI_nhdr,outfile=corr_DWI)
# # log_cmd= # # log_cmd+  unusaveCmd + '\n '
print unusaveCmd
os.system(unusaveCmd)
os.remove(corr_DWI_nhdr)
os.remove(corr_DWI_nhdr.replace('.nhdr','.raw'))
os.remove(orig_DWI_nhdr)
os.remove(B0_mnc)

#clean up
rmCmd = 'rm -rf '+os.path.join(orig_DWI_dir,'*mnitemp*')
print rmCmd
os.system(rmCmd)
rmCmd = 'rm -rf '+os.path.join(orig_DWI_dir,'*mri_nu*')
print rmCmd
os.system(rmCmd)

# f_log = open(corr_DWI_nhdr.replace('.nrrd','_log.txt'),'w');
# f_log.write(# log_cmd);
# f_log.close()







 
