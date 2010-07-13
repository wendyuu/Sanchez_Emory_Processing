#! /usr/bin/env python
# Prep_data should already generated T1, T2 nhdr and gipl.gz
# Script to do tissue segmentation using newly built atlas and ABC
# 
#
# Yundi Shi

import os
import sys
import fnmatch
import glob
from optparse import OptionParser

# VARIABLES SPECIFIC TO DATASET
ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
# the txt file that stores all the prefix names
# prefix of the file names
# either read it from a file or as input
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename",
                  help="read data from FILE", metavar="FILE")
parser.add_option("-a", "--age", dest="age",
                  help="age of the group")
parser.add_option("-n", "--newatlas", dest="newatlas",default=False,action="store_true",
                  help="Use the newly built atlas -- Emory data based and age specific")

(options, args) = parser.parse_args()

#read in the subjects that need to be handled
if options.filename:
   print 'Reading input from file '+options.filename
   prefixfile = os.path.join(ORIG_DATA_DIR,'processing',options.filename);
   prefixlist = open(prefixfile,'r');
elif len(args) > 0:
   print 'Reading input from the terminal'
   prefixlist = args;
   print args
else:
   print ('Input error: Either give a file name to read the prefix names of the subjects or type in from the terminal')

if options.age:
      age = options.age
      
# LOCATION VARIABLES for the atlas/template
# SYSTEM VARIABLES
#commands and locations of the template, etc.
from string import Template
SlicerLoc = '/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64/'
TatlasLoc = Template('/primate/SanchezEmory/BrainDevYerkes/sMRIatlas/${age}/T1/Areg2template/all_subjects/sAtlas') #new atlas built with Emory data
atlasLoc = ('/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/ABC_stripped/') #old atlas from CoeMonkey data

#BRAINS registration
BRAINSFitCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/BRAINSFit --movingVolume $sou --fixedVolume $tar --outputTransform $trans')) 

#rview registration
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TrregCmd = Template('/tools/rview_linux64_2008/rreg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
# the txt file that stores all the prefix names
parfile = os.path.join(ORIG_DATA_DIR ,'processing/Reg_par_NMI_Bspline.txt')

TintensityRescaleCmd = Template('/tools/bin_linux64/IntensityRescaler')
TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
TbiascorrectCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/N4ITKBiasFieldCorrection --inputimage $infile --outputimage $outfile'))
TunugzipCmd = Template(os.path.join(SlicerLoc,'bin/unu')+' save -f nrrd -e gzip -i $infile -o $outfile')
TunuClampCmd = Template(os.path.join(SlicerLoc,'bin/unu')+' 3op clamp $min  $infile $max -o $outfile')
ABCCmd = '/tools/bin_linux64/ABC' #ABC



###############################################################
##########################PIPELINE#############################
########1. N4 CORRECTION
########2. RIGID REGISTRATION (T1 to Atlas, T2 to T1)
########3. ABC
########4. SKULL STRIPPING
########5. INTENSITY CALIBRATION

# loop through the folders to calculate tensor
for prefix in prefixlist:
    prefix = prefix[0:5]
    SUBJ_DIR =  os.path.join(ORIG_DATA_DIR,prefix,age)
    
    if(options.newatlas == True): #Use new atlas
       atlasLoc = TatlasLoc.substitute(age=age)
    else:
       pass
    #For each subject
    
    if os.path.exists(SUBJ_DIR):
       print prefix
       sMRI_DIR = os.path.join(SUBJ_DIR,'sMRI')
       TISSUE_SEG_DIR = os.path.join(sMRI_DIR,'Tissue_Seg_ABC')
       if(os.path.exists(TISSUE_SEG_DIR)==False):
          os.mkdir(TISSUE_SEG_DIR)
       
       #log file of all the commands
       log_file = os.path.join(sMRI_DIR,'log_ABCSEG.txt')
       log = ''
       # generate first step nrrd files
       # for old files that only has 050505mm but not 060606mm
       T1_nrrd = os.path.join(sMRI_DIR,prefix+'_'+age+'_T1_050505mm.nrrd')
       T2_nrrd = os.path.join(sMRI_DIR,prefix+'_'+age+'_T2_050510mm.nrrd')
       for sMRI in ['T1','T2']:
          sMRI_nrrd = eval(sMRI+'_nrrd')
          sMRI_nhdr = sMRI_nrrd.replace('.nrrd','.nhdr')
          sMRI_raw = sMRI_nrrd.replace('.nrrd','.raw')
          sMRI_rawgz = sMRI_nrrd.replace('.nrrd','.raw.gz')
          sMRI_temp = os.path.join(sMRI_DIR,prefix+'_'+age+'_'+sMRI+'.nrrd')
          if (os.path.exists(sMRI_nrrd)==False):
             if(os.path.exists(sMRI_nhdr)==True):
                unugzipCmd = TunugzipCmd.substitute(infile=sMRI_nhdr,outfile=sMRI_nrrd)
                print unugzipCmd
                os.system(unugzipCmd)
             elif(os.path.exists(sMRI_temp)==True):
                unugzipCmd = TunugzipCmd.substitute(infile=sMRI_temp,outfile=sMRI_nrrd)
                print unugzipCmd
                os.system(unugzipCmd)
             else:
                sys.exit("where is the "+sMRI)      
          #clean-up
          if(os.path.exists(sMRI_temp)): os.remove(sMRI_temp)
          if(os.path.exists(sMRI_nhdr)): os.remove(sMRI_nhdr)
          if(os.path.exists(sMRI_raw)): os.remove(sMRI_raw)
          if(os.path.exists(sMRI_rawgz)): os.remove(sMRI_rawgz)

       #T1 and T2 already in RAI space
       T1_N4 = T1_nrrd.replace('.nrrd','_N4corrected.nrrd')
       T2_N4 = T2_nrrd.replace('.nrrd','_N4corrected.nrrd')
                                                                       
       # Bias field correction
       #2) Apply the N4 correction
       for sMRI in ['T1','T2']:
          biascorrectCmd = TbiascorrectCmd.substitute(infile=eval(sMRI+'_nrrd'),outfile=eval(sMRI+'_N4'))
          log = log + biascorrectCmd + '\n\n'
          if (os.path.exists(eval(sMRI+'_N4'))==False):
             print biascorrectCmd
             os.system(biascorrectCmd)
       
       # Register T2 to T1
       T2RregT1  = T2_N4.replace('.nrrd','_RregT1.nrrd')
       TransRreg = T2RregT1.replace('.nrrd','_trans.txt')
       
       BFitCmd = BRAINSFitCmd.substitute(tar = T1_N4, sou = T2_N4, trans = TransRreg) + ' --transformType Rigid --useCenterOfHeadAlign --interpolationMode BSpline ----outputVolume ' + T2RregT1
       log = log + BFitCmd + '\n\n'
       if (os.path.exists(TransRreg) == False):
          print BFitCmd
          os.system(BFitCmd)
       #Get rid of the negative parts
       clampCmd = TunuClampCmd.substitute(infile = T2RregT1, outfile = T2RregT1, min = 0, max = 1000000)
       log = log + clampCmd + '\n\n'
       print clampCmd
       os.system(clampCmd)

       T1_ABC = T1_N4.replace(sMRI_DIR,TISSUE_SEG_DIR).replace('.nrrd','_ABCStripped.nrrd')
       T1_ABC_ini = T1_N4.replace(sMRI_DIR,TISSUE_SEG_DIR).replace('.nrrd','_ABCStripped_ini.nrrd')
       T2_ABC = T2RregT1.replace(sMRI_DIR,TISSUE_SEG_DIR).replace('.nrrd','_ABCStripped.nrrd')
       T2_ABC_ini = T2RregT1.replace(sMRI_DIR,TISSUE_SEG_DIR).replace('.nrrd','_ABCStripped_ini.nrrd')
       brainmask = os.path.join(TISSUE_SEG_DIR,'ABC_brainMask.nrrd')
       
       if (os.path.exists(T1_ABC) == False or os.path.exists(T2_ABC) == False):
          for SUFFIX in ['ABC_ini','ABC']:
             if(SUFFIX == 'ABC_ini'):
                #initial stull stripping
                infile1 = T2RregT1
                infile2 = T1_N4
                outfile1 = eval('T2_'+SUFFIX)
                outfile2 = eval('T1_'+SUFFIX)
             else:
                infile1 = T1_ABC_ini
                infile2 = T2_ABC_ini
                outfile1 = eval('T1_'+SUFFIX)
                outfile2 = eval('T2_'+SUFFIX)
                
             # 3. perform ABC based segmentation
             ABC_file = os.path.join(TISSUE_SEG_DIR,SUFFIX+'_param.xml')
             ABC_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+atlasLoc+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+TISSUE_SEG_DIR+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>Nrrd</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+infile1+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+infile2+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<FILTER-ITERATIONS>10</FILTER-ITERATIONS>\n\
<FILTER-TIME-STEP>0.01</FILTER-TIME-STEP>\n\
<FILTER-METHOD>Curvature flow</FILTER-METHOD>\n\
<MAX-BIAS-DEGREE>2</MAX-BIAS-DEGREE>\n\
<PRIOR>1.2</PRIOR>\n\
<PRIOR>1</PRIOR>\n\
<PRIOR>0.7</PRIOR>\n\
<PRIOR>1</PRIOR>\n\
<DO-ATLAS-WARP>0</DO-ATLAS-WARP>\n\
<ATLAS-WARP-FLUID-ITERATIONS>1</ATLAS-WARP-FLUID-ITERATIONS>\n\
\n\
<!-- Mapping types: default is affine, can be rigid or id instead -->\n\
<ATLAS-LINEAR-MAP-TYPE>affine</ATLAS-LINEAR-MAP-TYPE>\n\
<IMAGE-LINEAR-MAP-TYPE>id</IMAGE-LINEAR-MAP-TYPE>\n\
\n\
</SEGMENTATION-PARAMETERS>\n'
  
             f = open(ABC_file,'w')
             f.write(ABC_info)
             f.close()
       
             # 3-2 run ABC
             cmd = ABCCmd + ' ' + ABC_file
             log = log + cmd + '\n\n'
             if (fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*'+SUFFIX+'.nrrd*') == []):
                os.system(cmd)
          
             #Use the label file to generate the brain mask
             for img in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*labels_'+SUFFIX+'.nrrd'):
                brainmaskIn = os.path.join(TISSUE_SEG_DIR,img)
                cmd = 'SegPostProcess ' + brainmaskIn + ' -o ' + brainmask + ' -v'
                log = log + cmd + '\n\n'
                if(os.path.exists(brainmask)==False):
                   print
                   os.system(cmd)
             
             #Skull stripping using the brain mask
             for loop in ['1','2']:
                ImageMathCmd = TImageMathCmd.substitute(infile = eval('infile'+loop), outfile = eval('outfile'+loop)) + ' -mask ' + brainmask
                log = log + ImageMathCmd + '\n\n'
                print ImageMathCmd
                os.system(ImageMathCmd)
	
       #write log file of all the commands
       f = open(log_file,'w')
       f.write(log)
         


