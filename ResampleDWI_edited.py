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
import string

print 'Usage:\n\
ResampleDWI.py \n\
[DWI (in nhdr or nrrd)] \n\
[DWI_resampled (name of DWI_resampled)] \n\
[scale (upsample>1, downsample<1))]\n'

# Commands:
TcvtCmd = string.Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TresampleCmd = string.Template('/devel/linux/Slicer3_linux64/Slicer3-build/lib/Slicer3/Plugins/ResampleVolume2 $sou $out -s $spc -z $dim -i ws -W h')
#/devel/linux/Slicer3_linux64/Slicer3-build/Libs
#'/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/lib/Slicer3/Plugins/ResampleVolume2 $sou $out -s $spc -z $dim -i ws -W h'

DWI_orig = sys.argv[1];
DWI_resampled = sys.argv[2];
scale = float(sys.argv[3]);

#print "DWI_orig = " + DWI_orig
#print "DWI_resampled = " + DWI_resampled
#print "scale = " + str(scale)

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
#for num in range(1,3):
#    eval('spacing'+num+'_resampled') = eval('spacing'+num+'_orig')/scale;
#    eval('dim'+num+'_resampled') = int(eval('dim'+num+'_orig')*scale);
spacing1_resampled = spacing1_orig/scale;
dim1_resampled = int(dim1_orig*scale);
spacing2_resampled = spacing2_orig/scale;
dim2_resampled = int(dim2_orig*scale);
spacing3_resampled = spacing3_orig/scale;
dim3_resampled = int(dim3_orig*scale);

# verbose information
print 'Resample the Volume from \n\
  (SIZE)   '+str(dim1_orig)+'*'+str(dim2_orig)+'*'+str(dim3_orig)+' to '+str(dim1_resampled)+'*'+str(dim2_resampled)+'*'+str(dim3_resampled)+'\n\
 (SPACING) '+str(spacing1_orig)+'*'+str(spacing2_orig)+'*'+str(spacing3_orig)+' to '+str(spacing1_resampled)+'*'+str(spacing2_resampled)+'*'+str(spacing3_resampled)

# input in nhdr format or nrrd format
DWI_orig_nhdr = DWI_orig.replace('nrrd','nhdr');
DWI_orig_nrrd = DWI_orig.replace('nhdr','nrrd');
# output in nhdr or nrrd
DWI_resampled_nhdr = DWI_resampled.replace('nrrd','nhdr');
DWI_resampled_nrrd = DWI_resampled.replace('nhdr','nrrd');

# to get input in both nhdr and nrrd format
if(fnmatch.fnmatch(DWI_orig,'*.nrrd') == True):
    cvtCmd = TcvtCmd.substitute(infile=DWI_orig,outfile=DWI_orig_nhdr);
    os.system(cvtCmd)
    DWI_orig_nrrd = DWI_orig;
    DWI_extra = DWI_orig_nhdr;  #DWI_extra is the one that needs to be deleted afterwards
elif(fnmatch.fnmatch(DWI_orig,'*.nhdr') == True):
    cvtCmd = TcvtCmd.substitute(infile=DWI_orig,outfile=DWI_orig_nrrd);
    os.system(cvtCmd)
    DWI_orig_nhdr = DWI_orig
    DWI_extra = DWI_orig_nrrd
else:
    sys.exit('Please convert the input into NRRD or NHDR using convertITKformats')

#DEBUG
#print "DWI_resampled_nhdr = " + DWI_resampled_nhdr
#print "DWI_resampled_nrrd = " + DWI_resampled_nrrd
#sys.exit(1)


# 1) Use ResampleVolume2 to resample nrrd
print '1) Use ResampleVolume2 to resample nrrd\n'
resampleCmd = TresampleCmd.substitute(sou=DWI_orig_nrrd,out=DWI_resampled_nrrd,spc=str(spacing1_resampled)+','+str(spacing2_resampled)+','+str(spacing3_resampled),dim=str(dim1_resampled)+','+str(dim2_resampled)+','+str(dim3_resampled))
print resampleCmd
os.system(resampleCmd)

# 2) Use convertITKformat to convert it to nhdr
print '2) Use convertITKformat to convert it to nhdr\n'
cvtCmd = TcvtCmd.substitute(infile=DWI_resampled_nrrd,outfile=DWI_resampled_nhdr);
os.system(cvtCmd)

# 3) manually rewrite the header file (DOESN'T SEEM TO WORK -GH)
print '3) manually rewrite the header file \n'
hdr_resampled = ''; 
fnhdr = open(DWI_orig_nhdr,'r')
for line in fnhdr:
    # change the sizing in the header file
    if(fnmatch.fnmatch(line,'sizes:*')):
    	print hdr_resampled + 'sizes: '+str(dim1_resampled)+' '+str(dim2_resampled)+' '+str(dim3_resampled)+ ' '+line.split(' ')[4]
        hdr_resampled = hdr_resampled + 'sizes: '+str(dim1_resampled)+' '+str(dim2_resampled)+' '+str(dim3_resampled)+ ' '+line.split(' ')[4]
    elif(fnmatch.fnmatch(line,'dimension:*')):
       hdr_resampled = hdr_resampled + line;
    
