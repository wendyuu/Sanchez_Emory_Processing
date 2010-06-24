#! /usr/bin/env python
# Script to generate parcelletation besed on T1/T2 atlas and the old atlas stored at
# /tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template???.gipl
# 

# Yundi Shi

# An example to run this program 
# GenerateParc.py sAtlas (the atlas used in generating the parcellation)

import os
import math
import fnmatch
import sys

###############the folder where atlas is stored#############
atlas = sys.argv[1]
atlas_dir = os.path.dirname(atlas)
print 'Processing '+atlas_dir
############################################################

ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
# the list of subjects stored at folder "processing"

from string import Template
TrregCmd = Template('/tools/rview_linux64_2008/rreg $tar $sou')
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')

parfile_NMI = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_NMI.txt')
parfile_CC = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_CC.txt')
parfile_NMI_Bspline = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_NMI_Bspline.txt')
parfile_CC_Bspline = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_CC_Bspline.txt')
template_atlas =  ('/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template.gipl')
template_parc =  ('/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template_parc.gipl')
template_parc_vent =  ('/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template_parc_vent.gipl')

grid_template = atlas.replace('.nrrd','.gipl')
cmd = TconvCmd.substitute(infile=atlas,outfile=grid_template)
print cmd
os.system(cmd)

# using b-spline registration to transform the old atlas to T1
# store all the transformation in the processing folder
processing_dir = os.path.join(atlas_dir,'parc_areg');
if(os.path.exists(processing_dir)==False): os.system('mkdir '+processing_dir);
dof = atlas.replace(atlas_dir,processing_dir).replace('.nrrd','_transformation.dof');
print dof
if (os.path.exists(dof) == False):
   parfile = parfile_NMI_Bspline;
   if (fnmatch.fnmatch(atlas,'*T1*')):
      # use CC for t1 to t1 registration
      parfile = parfile_CC_Bspline
   rregCmd = TrregCmd.substitute(tar=grid_template,sou=template_atlas)+' -dofout '+dof+' -parin '+parfile+' -Tp 5';
   os.system(rregCmd);
   aregCmd = TaregCmd.substitute(tar=grid_template,sou=template_atlas)+' -dofin '+dof+' -dofout '+dof+' -parin '+ parfile+' -Tp 5 -p9';
   os.system(aregCmd);

# apply this transformation to the parcelletion
# construct grid template

# -------------IMPORTANT------------
# the label files should NOT be interpolated linearly
# Using nearest neighbour
parc = atlas.replace('.nrrd','_parc.gipl.gz');
transformCmd = TtransformCmd.substitute(sou=template_parc,out=parc,dofin = dof)+' -target '+grid_template;
print transformCmd
os.system(transformCmd)
parc_vent = atlas.replace('.nrrd','_parc_vent.gipl.gz');
transformCmd = TtransformCmd.substitute(sou=template_parc_vent,out=parc_vent,dofin = dof)+' -target '+grid_template;
print transformCmd
os.system(transformCmd)
os.remove(grid_template)
