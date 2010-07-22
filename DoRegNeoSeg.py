#! /usr/bin/env python
# Prep_data should already generated T1, T2 nhdr and gipl.gz
# Script to do tissue segmentation using newly T2 atlas and neoseg
# 
#
# Yundi Shi


import os
import fnmatch
import glob
from optparse import OptionParser

# VARIABLES SPECIFIC TO DATASET
ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
ORIG_PROCESSING_DIR = os.path.join(ORIG_DATA_DIR,'Sanchez_Emory_Processing')
# the txt file that stores all the prefix names
# prefix of the file names
# either read it from a file or as input
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename",
                  help="read data from FILE", metavar="FILE")
parser.add_option("-a", "--age", dest="age",
                  help="age of the group")
parser.add_option("-o", "--oldatlas", dest="oldatlas",default=False,action="store_true",
                  help="Use the old Coemonkey altas")

(options, args) = parser.parse_args()

#read in the subjects that need to be handled
if options.filename:
   print 'Reading input from file '+options.filename
   prefixfile = os.path.join(ORIG_PROCESSING_DIR,options.filename)
   prefixlist = open(prefixfile,'r')
elif len(args) > 0:
   print 'Reading input from the terminal'
   prefixlist = args
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
TatlasLoc = Template('/primate/SanchezEmory/BrainDevYerkes/sMRIatlas/${age}/T2/Areg2template/all_subjects/sAtlas') #new atlas built with Emory data
atlasLoc = ('/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/ABC_stripped/') #old atlas from CoeMonkey data
rigidatlas = '/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template.gipl'

#BRAINS registration
BRAINSFitCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/BRAINSFit --movingVolume $sou --fixedVolume $tar --outputTransform $trans'))
BRAINSResampleCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/BRAINSResample --warpTransform $trans --interpolationMode BSpline --outputVolume $out --inputVolume $sou --referenceVolume $tar'))

TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
TbiascorrectCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/N4ITKBiasFieldCorrection --inputimage $infile --outputimage $outfile'))
TunugzipCmd = Template(os.path.join(SlicerLoc,'bin/unu')+' save -f nrrd -e gzip -i $infile -o $outfile')
TunuClampCmd = Template(os.path.join(SlicerLoc,'bin/unu')+' 3op clamp $min  $infile $max -o $outfile')
TChangeOrigin = Template(os.path.join(ORIG_PROCESSING_DIR,'ChangeOrigin.py $file $file'))

#neoseg
NEOSEGCmd = '/tools/bin_linux64/neoseg_1.7'
NEOSEGT1warp_orig = os.path.join(ORIG_PROCESSING_DIR,'T1name_to_template_EMSinfo.affine')
NEOSEGT2warp_orig = os.path.join(ORIG_PROCESSING_DIR,'T1name_to_T2name_EMSinfo.affine')

# loop through the folders to calculate tensor
for prefix in prefixlist:
    prefix = prefix[0:5]
    SUBJ_DIR =  os.path.join(ORIG_DATA_DIR,prefix,age)    
    if(options.oldatlas == False): #Use new atlas
       atlasLoc = TatlasLoc.substitute(age=age)
    else:
       pass
    atlasFile = os.path.join(atlasLoc,'templateT2.gipl.gz')
    #For each subject
    
    if os.path.exists(SUBJ_DIR):
       sMRI_DIR = os.path.join(SUBJ_DIR,'sMRI')
       TISSUE_SEG_DIR = os.path.join(sMRI_DIR,'Tissue_Seg_NEOSEG')
       if(os.path.exists(TISSUE_SEG_DIR)==False):
          os.mkdir(TISSUE_SEG_DIR)
       
       #log file of all the commands
       log_file = os.path.join(sMRI_DIR,'log_NEOSEG.txt')
       log = ''
       # generate first step nrrd files
       T1_05_nrrd = os.path.join(sMRI_DIR,prefix+'_'+age+'_T1_050505mm.nrrd')
       T1_06_nrrd = os.path.join(sMRI_DIR,prefix+'_'+age+'_T1_060606mm.nrrd')
       T2_nrrd = os.path.join(sMRI_DIR,prefix+'_'+age+'_T2_050510mm.nrrd')

       for sMRI in ['T1_05','T1_06','T2']:
          sMRI_nrrd = eval(sMRI+'_nrrd')
          if(os.path.exists(sMRI_nrrd)):
             sMRI_nrrd = eval(sMRI+'_nrrd')
             unugzipCmd = TunugzipCmd.substitute(infile=sMRI_nrrd,outfile=sMRI_nrrd)
             print unugzipCmd
             os.system(unugzipCmd)
       #######################################
       # 1. Bias field correction using N4
       ######################################
       #Apply the N4 correction
       for sMRI in ['T1_05','T1_06','T2']:
          if(os.path.exists(eval(sMRI+'_nrrd'))):
             biascorrectCmd = TbiascorrectCmd.substitute(infile=eval(sMRI+'_nrrd'),outfile=eval(sMRI+'_nrrd').replace('.nrrd','_N4corrected.nrrd'))
             log = log + biascorrectCmd + '\n\n'
             if (os.path.exists(eval(sMRI+'_nrrd').replace('.nrrd','_N4corrected.nrrd'))==False):
                print biascorrectCmd
                os.system(biascorrectCmd)
             #change the origin to 0,0,0 for registration later
             cmd = TChangeOrigin.substitute(file=eval(sMRI+'_nrrd').replace('.nrrd','_N4corrected.nrrd'))
             log = log + cmd + '\n\n'
             print cmd
             os.system(cmd)

        ################################
       # 2. Rigid Registration
       ################################
       #T1 and T2 already in RAI space
       # for old files that only has 050505mm but not 060606mm
       # Use 06 T1
       if (os.path.exists(T1_06_nrrd) == True):
          T1_nrrd = T1_06_nrrd
       else:
          T1_nrrd = T1_05_nrrd
       T1_N4 = T1_nrrd.replace('.nrrd','_N4corrected.nrrd')
       T2_N4 = T2_nrrd.replace('.nrrd','_N4corrected.nrrd')
       Rreg2atlas_DIR = os.path.join(sMRI_DIR,'Rreg2Atlas')
       if(os.path.exists(Rreg2atlas_DIR)==False): os.mkdir(Rreg2atlas_DIR)

       T1RregAtlas = T1_N4.replace('.nrrd','_Rreg2Atlas.nrrd').replace(sMRI_DIR,Rreg2atlas_DIR)
       T2RregT1  = T2_N4.replace('.nrrd','_Rreg2T1Atlas.nrrd').replace(sMRI_DIR,Rreg2atlas_DIR)
       T1TransRreg = T1RregAtlas.replace('.nrrd','_trans.txt')
       T2TransRreg = T2RregT1.replace('.nrrd','_trans.txt')

       #register T1 to atlas
       BFitCmd = BRAINSFitCmd.substitute(tar = rigidatlas, sou = T1_N4, trans = T1TransRreg) + ' --transformType Rigid --interpolationMode BSpline --useCenterOfHeadAlign --outputVolumePixelType short --outputVolume ' + T1RregAtlas
       log = log + BFitCmd + '\n\n'
       clampCmd = TunuClampCmd.substitute(infile = T1RregAtlas, outfile = T1RregAtlas, min = 0, max = 1000000)
       log = log + clampCmd + '\n\n'
       if (os.path.exists(T1TransRreg) == False):
          print BFitCmd
          os.system(BFitCmd)
          #Get rid of the negative parts
          print clampCmd
          os.system(clampCmd)

       #register T2 to atlas-registered T1
       BFitCmd = BRAINSFitCmd.substitute(tar = T1RregAtlas, sou = T2_N4, trans = T2TransRreg) + ' --transformType Rigid --interpolationMode BSpline --outputVolumePixelType short --outputVolume ' + T2RregT1
       log = log + BFitCmd + '\n\n'
       clampCmd = TunuClampCmd.substitute(infile = T2RregT1, outfile = T2RregT1, min = 0, max = 1000000)
       log = log + clampCmd + '\n\n'
       if (os.path.exists(T2TransRreg) == False):
          print BFitCmd
          os.system(BFitCmd)
          #Get rid of the negative parts
          print clampCmd
          os.system(clampCmd)

       regtar = 'T2RregT1'
       SUFFIX = 'NEOSEG'
       NEOSEGreg = 0
       NEOSEGfile  = os.path.join(TISSUE_SEG_DIR,(SUFFIX+'param.xml')) 
       if (NEOSEGreg == 0):
         # trick to disable warping in NEOSEG
         # cp the transformation file with identity trans to the tmp folder

         NEOSEGT1warp_tar = NEOSEGT1warp_orig.replace(ORIG_PROCESSING_DIR,TISSUE_SEG_DIR).replace('T1name',prefix+'_'+age+'_T2_050510mm_N4corrected_Rreg2T1Atlas').replace('EMSinfo',SUFFIX).replace('template','templateT2')
         NEOSEGT2warp_tar = NEOSEGT2warp_orig.replace(ORIG_PROCESSING_DIR,TISSUE_SEG_DIR).replace('T1name',prefix+'_'+age+  '_T2_050510mm_N4corrected_Rreg2T1Atlas').replace('T2name',prefix+'_'+age+  '_T1_050505mm_N4corrected_Rreg2Atlas').replace('EMSinfo',SUFFIX)
         os.system('cp '+ NEOSEGT1warp_orig + ' ' + NEOSEGT1warp_tar)
         os.system('cp '+ NEOSEGT2warp_orig + ' ' + NEOSEGT2warp_tar)

         # 1 - 1. affinely align atlas to the subject and make subject specific atlas
         newTemplate = atlasFile.replace(atlasLoc,TISSUE_SEG_DIR)
         TransAreg = newTemplate.replace('.gipl.gz','_areg2subject.txt')

         BFitCmd = BRAINSFitCmd.substitute(tar = eval(regtar), sou = atlasFile, trans = TransAreg) + ' --useCenterOfHeadAlign --interpolationMode BSpline --transformType Rigid,Affine --outputVolume ' + newTemplate
         log = log + BFitCmd + '\n\n'
         if (os.path.exists(TransAreg) == False):
            print BFitCmd
            os.system(BFitCmd)
         
         # 1 - 2. transform the template accordingly

         for parc in ['templateT2','white','gray','csf','rest','parcellation']:
            ems_parc = os.path.join(TISSUE_SEG_DIR,parc+'.gipl.gz')
            if (os.path.exists(ems_parc)==False):
               BResampleCmd = BRAINSResampleCmd.substitute(sou=atlasFile.replace('templateT2.gipl.gz',parc+'.gipl.gz'),out=ems_parc, tar = eval(regtar),trans = TransAreg)
               log = log + BResampleCmd + '\n\n'
               if (os.path.exists(ems_parc) == False):
                  print BResampleCmd
                  os.system(BResampleCmd)
            #Get rid of the negative parts
            ImageMathCmd = TImageMathCmd.substitute(infile = ems_parc, outfile = ems_parc) + ' -threshMask 0,1000000'
            log = log + ImageMathCmd + '\n\n'
            print ImageMathCmd
            os.system(ImageMathCmd)

         # 2. edit pixdims for all images in TISSUE_SEG_DIR
         # 2-1 Get the original pixel information
         origPixdim = os.popen('ImageStat '+eval(regtar)+' -info | grep Pixdims').read()
         origdim = os.popen('ImageStat '+eval(regtar)+' -info | grep Dims').read()
         origPixdims = str(origPixdim).split(' ')
         origdims = str(origdim).split(' ')

         # 2-2 Change pixdim to 1.0*1.0*1.0				
         for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*gipl.gz'):
              ImageMathCmd = TImageMathCmd.substitute(infile = os.path.join(TISSUE_SEG_DIR,image), outfile = os.path.join(TISSUE_SEG_DIR,image)) + ' -editPixdims 1.0,1.0,1.0'
              log = log + ImageMathCmd + '\n\n'
              os.system(ImageMathCmd)
              os.system('gunzip '+ os.path.join(TISSUE_SEG_DIR,image))
              
         ImageMathCmd = TImageMathCmd.substitute(infile = T1RregAtlas , outfile = T1RregAtlas) + ' -editPixdims 1.0,1.0,1.0'
         log = log + ImageMathCmd + '\n\n'
         os.system(ImageMathCmd)
         
         ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2RregT1) + ' -editPixdims 1.0,1.0,1.0'
         log = log + ImageMathCmd + '\n\n'
         os.system(ImageMathCmd)

         # 3. perform itkNEOSEG-based segmentation
         # 3-1 create NEOSEG file
         NEOSEG_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+TISSUE_SEG_DIR+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+TISSUE_SEG_DIR+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>NRRD</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+T2RregT1+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+T1RregAtlas+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<FILTER-ITERATIONS>10</FILTER-ITERATIONS>\n\
<FILTER-TIME-STEP>0.01</FILTER-TIME-STEP>\n\
<FILTER-METHOD>Curvature flow</FILTER-METHOD>\n\
<MAX-BIAS-DEGREE>0</MAX-BIAS-DEGREE>\n\
<PRIOR-1>0.2</PRIOR-1>\n\
<PRIOR-2>1.4</PRIOR-2>\n\
<PRIOR-3>1</PRIOR-3>\n\
<PRIOR-4>0.5</PRIOR-4>\n\
<PRIOR-5>1</PRIOR-5>\n\
<DO-ATLAS-WARP>0</DO-ATLAS-WARP>\n\
<ATLAS-WARP-GRID-X>5</ATLAS-WARP-GRID-X>\n\
<ATLAS-WARP-GRID-Y>5</ATLAS-WARP-GRID-Y>\n\
<ATLAS-WARP-GRID-Z>5</ATLAS-WARP-GRID-Z>\n\
<MAHALANOBIS-THRESHOLD>2</MAHALANOBIS-THRESHOLD>\n\
<PARZEN-KERNEL-WIDTH>0.05</PARZEN-KERNEL-WIDTH>\n\
<PRIOR-THRESHOLD>0.8</PRIOR-THRESHOLD>\n\
<REFERENCE-IMAGE-INDEX>1</REFERENCE-IMAGE-INDEX>\n\
<REFERENCE-MODALITY>T2</REFERENCE-MODALITY>\n\
</SEGMENTATION-PARAMETERS>\n'                    
         fout = open(NEOSEGfile,'w')
         fout.write(NEOSEG_info)
         fout.close()

         if (os.path.exists(os.path.join(TISSUE_SEG_DIR,'*_NEOSEG*.gipl*')) == False or options.NEOSEG == True):
              # 3-2 run neoseg
              cmd = NEOSEGCmd + ' ' + NEOSEGfile
              log = log + cmd + '\n\n'
              os.system(cmd)

              # 3-5 edit back the pixel size
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*gipl*'):
                 ImageMathCmd = TImageMathCmd.substitute(infile = os.path.join(TISSUE_SEG_DIR,image), outfile = os.path.join(TISSUE_SEG_DIR,image)) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
                 log = log + ImageMathCmd + '\n\n'
                 os.system(ImageMathCmd)
                 os.system('gzip '+os.path.join(TISSUE_SEG_DIR,image))
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*nrrd'):
                 ImageMathCmd = TImageMathCmd.substitute(infile = os.path.join(TISSUE_SEG_DIR,image), outfile = os.path.join(TISSUE_SEG_DIR,image)) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
                 log = log + ImageMathCmd + '\n\n'
                 os.system(ImageMathCmd)
                 cmd = TunugzipCmd.substitute(infile=os.path.join(TISSUE_SEG_DIR,image),outfile = os.path.join(TISSUE_SEG_DIR,image))
                 log = log + cmd + '\n\n'
                 os.system(cmd)
              ImageMathCmd = TImageMathCmd.substitute(infile = T1RregAtlas, outfile = T1RregAtlas) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
              log = log + ImageMathCmd + '\n\n'
              os.system(ImageMathCmd)
              ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2RregT1) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
              log = log + ImageMathCmd + '\n\n'
              os.system(ImageMathCmd)
       
