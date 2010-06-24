#! /usr/bin/env python

# Script to resample DWI volumes 
# 1) Use ResampleVolume2 to resample nrrd
# 2) Use convertITKformat to convert it to nhdr
# 3) manually rewrite the header file
# Yundi Shi

import os
import fnmatch
import glob
import sys

print 'Usage:\n\
ResampleDWI.py \n\
[DWI (in nhdr or nrrd)] \n\
[DWI_resampled (name of DWI_resampled)] \n\
[scale (upsample>1, downsample<1))]\n'

# Commands:
TcvtCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TresampleCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/lib/Slicer3/Plugins/ResampleVolume2 $sou $out -s $spc -z $dim -i ws -W h')

DWI_orig = sys.argv[1];
DWI_resampled = sys.argv[2];
scale = float(sys.argv[3]);

# Get the original spacing and dimension
#spacing
origPixdim = os.popen('ImageStat '+ DWI_orig+' -info | grep Pixdims').read()
origPixdims = str(origPixdim).split(' ');
spacing1_orig = float(origPixdims[1]);
spacing2_orig = float(origPixdims[2]);
spacing3_orig = float(origPixdims[3].replace('\n',''));
#dimension
origdim = os.popen('ImageStat '+DWI_orig+' -info | grep Dims').read()
origdims = str(origdim).split(' ');
dim1_orig = float(origdims[1]);
dim2_orig = float(origdims[2]);
dim3_orig = float(origdims[3].replace('\n',''));

# calculate the resampled spacing and dimension
for num in range(1,3):
    eval('spacing'+num+'_resampled') = eval('spacing'+num+'_orig')/scale;
    eval('dim'+num+'_resampled') = int(eval('dim'+num+'_orig')*scale);
# verbose information
print 'Resample the Volume from \n\
  (SIZE)   '+dim1_orig+'*'+dim2_orig+'*'+dim3_orig+' to '+dim1_oresampled+'*'+dim2_resampled+'*'+dim3_resampled+'\n\
 (SPACING) '+spacing1_orig+'*'+spacing2_orig+'*'+spacing3_orig+' to '+spacing1_resampled+'*'+spacing2_resampled+'*'+spacing3_resampled

# input in nhdr format or nrrd format
DWI_orig_nhdr = DWI_orig.replace('nrrd','nhdr');
DWI_orig_nrrd = DWI_orig.replace('nhdr','nrrd');
# output in nhdr or nrrd
DWI_resampled_nhdr = DWI_resampled.replace('nrrd','nhdr');
DWI_resampled_nrrd = DWI_resampled.replace('nhdr','nrrd');

# to get input in both nhdr and nrrd format
if(fnmatch.fnmatch(DWI_orig,'nrrd') == True):
    cvtCmd = TcvtCmd.substitute(sou=DWI_orig,tar=DWI_orig_nhdr);
    os.system(cvtCmd)
    DWI_orig_nrrd = DWI_orig;
    DWI_extra = DWI_orig_nhdr;  #DWI_extra is the one that needs to be deleted afterwards
elif(fnmatch.fnmatch(DWI_orig,'nhdr') == True):
    cvtCmd = TcvtCmd.substitute(sou=DWI_orig,tar=DWI_orig_nrrd);
    os.system(cvtCmd)
    DWI_orig_nhdr = DWI_orig
    DWI_extra = DWI_orig_nrrd
else:
    sys.exit('Please convert the input into NRRD or NHDR using convertITKformats')

# 1) Use ResampleVolume2 to resample nrrd
print '1) Use ResampleVolume2 to resample nrrd\n'
resampleCmd = TresampleCmd.substitute(sou=DWI_orig_NRRD,out=DWI_resampled_nrrd,spc=spacing1_resampled+','+spacing2_resampled+','+spacing3_resampled,dim=dim1_resampled+','+dim2_resampled+','+dim3_resampled)
print resampleCmd
os.system(resampleCmd)

# 2) Use convertITKformat to convert it to nhdr
print '2) Use convertITKformat to convert it to nhdr\n'
cvtCmd = TcvtCmd.substitute(sou=DWI_resampled_nrrd,tar=DWI_resampled_nhdr);
os.system(cvtCmd)

# 3) manually rewrite the header file
print '3) manually rewrite the header file \n'
hdr_resampled = ''; 
fnhdr = fopen(DWI_orig_nhdr,'r')
for line in fnhdr:
    # change the sizing in the header file
    if(fnmatch.fnmatch(line,'sizes:'):
       hdr_resampled = hdr_resampled + 'sizes: '+dim1_resampled+' '+dim2_resampled+' '+dim3_resampled+ ' '+line.split(' ')[4]
    elif(fnmatch.fnmatch(line,'sizes:'):
       hdr_resampled = hdr_resampled + line;
    
