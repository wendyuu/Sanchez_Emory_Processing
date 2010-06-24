#! /usr/bin/env python
# Script to fwarp several subject to one using fwarp
#
# Yundi Shi

import os
import math
import fnmatch
import sys

from optparse import OptionParser

ROOT_DIR = '/primate/SanchezEmory/BrainDevYerkes/'

##################################################################################
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-a", "--age", dest="age", help="age")
parser.add_option("-t", "--target", dest="tar", help="target image")
parser.add_option("-s", "--source", dest="sou_list", help = "list of source images")

(options, args) = parser.parse_args()
if options.tar and options.sou_list and options.age:
    tar = options.tar
    sou_list = options.sou_list.split(',')
    age = options.age
else:
    print "Usage: \n\
    fWarp_Subject \n\
    --target -t [tar]\n\
    --source -s [sou1,sou2,sou3...]\n\
    --age -a [age]\n"
    sys.exit('Please read the usage and do it again')
    
from string import Template
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TunucvtCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu convert -i $infile -o $outfile');
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -i $file -o $file');
TImageMathcvtCmd = Template('/tools/bin_linux64/ImageMath $infile -constOper 0,0 -outfile $outfile');
ThistmatchCmd = Template('/tools/bin_linux64/ImageMath $sou -matchHistogram $tar -outfile $out')
Ttio1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransform.script $dof $txt')
TtioInv1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransformInv.script $dof $txt')
Ttio2Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/TransformCentered2NotCentered $txt $sou $tar $txt')
Ttio3Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/Double2FloatTransform.script $txtin $txtout')
TcurvCmd = Template('/tools/bin_linux64/maxcurvature $FA -o $curvFA')
#TCenterImage = Template('/primate/SanchezEmory/BrainDevYerkes/processing/ChangeOrigin.py $infile $outfile')
TChangeSpaceDir = Template('/primate/SanchezEmory/BrainDevYerkes/processing/ChangeSpaceDir.py $infile $outfile')
THfieldFixUp = Template('/primate/SanchezEmory/BrainDevYerkes/processing/HfieldFixUp.py $Hfield $Img')
ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
Template_Dir = '/primate/SanchezEmory/BrainDevYerkes/Template_CoeMonkeyFlu/'
DTIprocess = '/tools/bin_linux64/dtiprocess'
DTIaverage = '/tools/bin_linux64/dtiaverage'
ResampleDTI = '/home/budin/LocalWork/ResampleDTIlogEuclidean-linux64/ResampleDTIlogEuclidean'

# parameters for affine transformation
parfile_NMI = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_NMI.txt')
parfile_CC = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_CC.txt')
parfile = parfile_CC


Atlas_DIR = os.path.join(ROOT_DIR,'DTIAtlas_Upsampled',age)
fWarp_DIR_parent = os.path.join(Atlas_DIR,'fWarp')
if(os.path.exists(fWarp_DIR_parent)==False): os.mkdir(fWarp_DIR_parent)
fWarp_DIR = os.path.join(fWarp_DIR_parent,tar);
if(os.path.exists(fWarp_DIR)==False): os.mkdir(fWarp_DIR)
Img_DIR = os.path.join(Atlas_DIR,'origImage')


#parameters for fWarp
###############################
# 6months parameters
numiter = [100, 50, 40];
alpha = [0.5, 0.5, 0.2];
beta = [0.5, 0.5, 0.2];
gamma = [0.1, 0.1, 0.05];
maxPerturbation = [0.2, 0.1, 0.1];
FAwin = [10, 120]

Histmatch_dir = os.path.join(fWarp_DIR,'histmatched')
if(os.path.exists(Histmatch_dir)==False): os.mkdir(Histmatch_dir)

Areg_dir = os.path.join(fWarp_DIR,'areg')
if(os.path.exists(Areg_dir)==False): os.mkdir(Areg_dir)

deformed_dir = os.path.join(fWarp_DIR,'deformed')
if(os.path.exists(deformed_dir)==False): os.mkdir(deformed_dir)
outDeformed = os.path.join(deformed_dir,'deformedImage_');
    
Hfield_dir = os.path.join(fWarp_DIR,'HField');
if(os.path.exists(Hfield_dir)==False): os.mkdir(Hfield_dir)
HField = os.path.join(Hfield_dir,'fHField_');

##################################################################################
    
##################Preparation before affine registration##########################

FA_tar =  os.path.join(Img_DIR,fnmatch.filter(os.listdir(Img_DIR),'FA_'+tar+'*gipl.gz')[0]);

FAlist = ' ';
for sou in sou_list:
    print 'Register '+ sou + ' to '+tar +' at age '+age
    fWarpfile = os.path.join(fWarp_DIR,'fWarp_'+sou+'_2'+tar+'.xml')
    f = open(fWarpfile,'w');

    FA = os.path.join(Img_DIR,fnmatch.filter(os.listdir(Img_DIR),'FA_'+sou+'*.gipl.gz')[0])
    # histogram matching
    FA_histmatched = FA.replace('.gipl.gz','_Histmatched2'+tar+'.gipl.gz').replace(Img_DIR,Histmatch_dir);
    if (os.path.exists(FA_histmatched) == False):
       print 'Histogram Matching of '+FA+' to '+FA_tar
       histmatchCmd = ThistmatchCmd.substitute(sou=FA,tar=FA_tar,out=FA_histmatched);
       os.system(histmatchCmd)
    # affine registration
    affine_tar = FA.replace('.gipl.gz','_IniAffine2'+tar+'.gipl.gz').replace(Img_DIR,Areg_dir);

    # Do affine transformation        
    dof = affine_tar.replace('.gipl.gz','.dof')
    txt = affine_tar.replace('.gipl.gz','_float.txt')
    txt_double = affine_tar.replace('.gipl.gz','_double.txt')

#     FA_affine_tar = FA_center.replace(Img_DIR,Areg_dir).replace('.nrrd','_IniAffine2'+tar_prefix+'.nrrd');
#     dti_affine_tar = dti_affine_sou.replace(Img_DIR,Areg_dir).replace('.nrrd','_IniAffine2'+tar_prefix+'.nrrd');
    # affine registration
    if (os.path.exists(dof) == False):
        print 'Affinely register '+FA_histmatched+' to '+FA_tar;
        AregCmd = TaregCmd.substitute(tar=FA_tar,sou=FA_histmatched)+' -dofout '+dof+' -parin '+parfile+' -p9 -Tp 5';
        os.system(AregCmd)
    # change dof to txt for atlaswerks to run
    tio_cmd = Ttio1Cmd.substitute(txt=txt_double,dof=dof)
    os.system(tio_cmd)
    print tio_cmd

    tio_cmd = Ttio2Cmd.substitute(txt=txt_double,sou=FA_histmatched,tar=FA_histmatched)
    os.system(tio_cmd)
    print tio_cmd

    tio_cmd = Ttio3Cmd.substitute(txtin=txt_double,txtout=txt)
    print tio_cmd
    os.system(tio_cmd)

    fWarpCmd = 'fWarp '+ FA_tar +' '+FA_histmatched+'\
 --outputImageFilenamePrefix='+outDeformed+'\
 --outputHFieldFilenamePrefix='+HField
    for slevel in [4, 2, 1]:
        index = 2-int(math.log(slevel,2));
        fWarpCmd = fWarpCmd + '\
 --scaleLevel='+str(slevel)+' --numberOfIterations='+str(numiter[index])+'\
 --alpha='+str(alpha[index])+'\
 --beta='+str(beta[index])+'\
 --gamma='+str(gamma[index])+'\
 --maxPerturbation='+str(maxPerturbation[index])
    fWarpCmd = fWarpCmd +'\
 --intensityWindowMin='+str(FAwin[0])+'\
 --intensityWindowMax='+str(FAwin[1])
    fWarpCmd = fWarpCmd +' '+txt;

    print fWarpCmd
    f.write(fWarpCmd.replace(' ','\n')+'\n'+'\n');
    fWarplog = os.path.join(fWarp_DIR,'fWarp_'+sou+'_2_'+tar+'.log')

    if(os.path.exists(fWarplog)==False):
        os.system(fWarpCmd+' 2>&1 |tee '+fWarplog)
    else:
        print 'Log Exists for fWarp... won\'t rerun'
    f.close()
