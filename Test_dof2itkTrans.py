#! /usr/bin/env python
# Script to test dof2itkTransform, etc scripts
#
# Yundi Shi

print 'Usage:\n\
Test_dof2itkTrans.py \n\
[\'sou_input1\'(Input Image)] \n\
[\'tar_input2\'(Input Image)] \n\
[\'trans\'(trans.dof, trans_double.txt,trans_float.txt)]\n\
[\'output(prefix)\'(output_Rview.gipl,output_ReSamVol2.gipl)] \n'

import os
import math
import fnmatch
import sys
from string import Template

##########Parameters used for atlas building regarding subject selection##########
sou = sys.argv[1];
tar = sys.argv[2];
trans = sys.argv[3];
output = sys.argv[4];
# if no : All subjects are used in atlas building
# if yes: a list of subject will be used for atlas building
###################################################################################
Ttio1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransform.script $dof $txt')
Ttio2Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/TransformCentered2NotCentered $txt $sou $tar $txt')
Ttio3Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/Double2FloatTransform.script $txt')
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin -target $tar')
TresampleCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/lib/Slicer3/Plugins/ResampleVolume2 $sou $out -f $txt -R $tar')
parfile = '/primate/SanchezEmory/BrainDevYerkes/processing/Reg_par_CC.txt'

#dof file after using areg
dof = trans + '.dof';
#txt file with float and double
txt_float = trans + '_float.txt';
txt_double = trans + '_double.txt';
#output image using rview transformation
output_Rv = output+'_Rview.gipl';
#output image using ResampleVolume2
output_Rs = output + 'ResamVol2.gipl';


#Using rview for areg
if(os.path.exists(dof)==False):
   print 'Affinely register '+sou+' to '+tar
   AregCmd = TaregCmd.substitute(tar=tar,sou=sou)+' -dofout '+dof+' -parin '+parfile+' -p9';
   os.system(AregCmd)

#Using rview for areg
print 'Change the transformation from dof to txt'
tio_cmd = Ttio1Cmd.substitute(txt=txt_double,dof=dof)
print tio_cmd
os.system(tio_cmd)
tio_cmd = Ttio2Cmd.substitute(txt=txt_double,sou=sou,tar=sou)
print tio_cmd
os.system(tio_cmd)

#Transform using rview
transformCmd = TtransformCmd.substitute(sou=sou,out=output_Rv,dofin=dof,tar=sou)+' -linear';
os.system(transformCmd)
print transformCmd
os.system(transformCmd)

#Transform using ResampleVolume2
resampleCmd = TresampleCmd.substitute(sou=sou,out=output_Rs,txt=txt_double,tar=sou)+' -i linear';
os.system(resampleCmd)
print resampleCmd
os.system(resampleCmd)
