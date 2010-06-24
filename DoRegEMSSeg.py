#! /usr/bin/env python
# Prep_data should already generated T1, T2 nhdr and gipl.gz
# Script to do tissue segmentation using newly built atlas and ABC
# 
#
# Yundi Shi

import os
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
parser.add_option("-a", "--age", dest="dir_tag",
                  help="age of the group")

(options, args) = parser.parse_args()

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

if options.dir_tag:
      dir_tag = options.dir_tag
      
# LOCATION VARIABLES for the atlas/template
EMST1warp_orig = os.path.join(ORIG_DATA_DIR,'processing/T1name_to_template_EMSinfo.affine');  
EMST2warp_orig = os.path.join(ORIG_DATA_DIR,'processing/T1name_to_T2name_EMSinfo.affine');
EMSReg = 0;
# SYSTEM VARIABLES
# usually DO NOT EDIT THESE
from string import Template
TatlasLoc = Template('/primate/SanchezEmory/BrainDevYerkes/sMRIatlas/${age}/T1/Areg2template/all_subjects/sAtlas')
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TrregCmd = Template('/tools/rview_linux64_2008/rreg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TintensityRescaleCmd = Template('/tools/bin_linux64/IntensityRescaler')
TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TwarpCmd = Template('/tools/bin_linux64/fWarp')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
TbiascorrectCmd = Template('/opt/local/Freesurfer_4_64/bin/mri_nu_correct.mni --i $infile --o $outfile')
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -i $infile -o $outfile');

#itk EMS without registration
itkEMSNoregCmd = '/tools/bin_linux/itkEMS_noReg'
itkEMS18Cmd = '/tools/bin_linux64/itkEMS_1.8'
ABCCmd = '/tools/bin_linux64/ABC'
#recompute montage pictures?
recomputeMontage = 1

# the txt file that stores all the prefix names
parfile = os.path.join(ORIG_DATA_DIR ,'processing/Reg_par_NMI_Bspline.txt')
# loop through the folders to calculate tensor
for prefix in prefixlist:
    prefix = prefix[0:5]
    SUBJ_DIR =  os.path.join(ORIG_DATA_DIR,prefix,dir_tag);
    atlasLoc = TatlasLoc.substitute(age=dir_tag);
    atlasFile = os.path.join(atlasLoc,'template.gipl.gz')
    if (os.path.exists(atlasFile)==False):
       os.system('gzip '+atlasFile.replace('.gipl.gz','.gipl'))
       
    print SUBJ_DIR
    if os.path.exists(SUBJ_DIR):
       
       sMRI_DIR = os.path.join(SUBJ_DIR,'sMRI');
       #gunzip everything
       for file in os.listdir(sMRI_DIR):
          if (fnmatch.fnmatch(file,'*gipl.gz')):
               cmd = 'gunzip '+os.path.join(sMRI_DIR,file)
               print cmd
               os.system(cmd)

       # generate first step nrrd files
       T1_temp = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T1.nrrd');
       T1_nrrd = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T1_050505mm.nrrd');
       if (os.path.exists(T1_nrrd)==False):
          unugzipCmd = TunugzipCmd.substitute(infile=T1_temp,outfile=T1_nrrd)
          print unugzipCmd
          os.system(unugzipCmd)
       T2_temp = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T2.nrrd');
       T2_nrrd = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T2_050510mm.nrrd');
       if (os.path.exists(T2_nrrd)==False):
          unugzipCmd = TunugzipCmd.substitute(infile=T2_temp,outfile=T2_nrrd)
          print unugzipCmd
          os.system(unugzipCmd)
       
       # Procedure
       # A) Bias field correction
       # B) Use EMS to do tissue segmentation
              #1) Register to the new atlas
              #2) Curve Smoothing
              #3) Init using rview manually
              #4) RunEMS
       # C) Warping etc

       # T1 and T2 RAI gipls
       T1_gipl = T1_nrrd.replace('.nrrd','.gipl');
       T2_gipl = T2_nrrd.replace('.nrrd','.gipl');
       if (os.path.exists(T1_gipl)==False):
          convCmd = TconvCmd.substitute(infile=T1_nrrd,outfile=T1_gipl)
          print convCmd
          os.system(convCmd)
       if (os.path.exists(T2_gipl)==False):
          convCmd = TconvCmd.substitute(infile=T2_nrrd,outfile=T2_gipl)
          print convCmd
          os.system(convCmd)

       T1 = T1_gipl.replace('.gipl','_RAI.gipl');
       T1_N3 = T1.replace('.gipl','_N3corrected.gipl')
       T2  = T2_gipl.replace('.gipl','_RAI.gipl');
       T2_N3 = T2.replace('.gipl','_N3corrected.gipl')
       
       if (os.path.exists(T1)==False):
          reorientCmd = TreorientCmd.substitute(infile = T1_gipl,outfile = T1);
          print reorientCmd + '-setorient LAI-RAI'
          os.system(reorientCmd + '-setorient LAI-RAI');
       if (os.path.exists(T1_gipl)):
          os.remove(T1_gipl)
          
       if (os.path.exists(T2)==False):
          reorientCmd = TreorientCmd.substitute(infile = T2_gipl,outfile = T2);
          print reorientCmd + '-setorient LAI-RAI'
          os.system(reorientCmd + '-setorient LAI-RAI');
       if (os.path.exists(T2_gipl)):
          os.remove(T2_gipl)
          
                                                                       
       # Bias field correction
       #2) Apply the mri_nu_correct
       if (os.path.exists(T1_N3)==False):
          #1) convert to .nii
          if (os.path.exists(T1.replace('.gipl','.nii'))==False):
             convCmd = TconvCmd.substitute(infile=T1,outfile=T1.replace('.gipl','.nii'))
             print convCmd
             os.system(convCmd)
          biascorrectCmd = TbiascorrectCmd.substitute(infile=T1.replace('.gipl','.nii'),outfile=T1_N3.replace('.gipl','.nii'))
          print biascorrectCmd
          os.system(biascorrectCmd)
          convCmd = TconvCmd.substitute(infile=T1_N3.replace('.gipl','.nii'),outfile=T1_N3)
          print convCmd
          os.system(convCmd)
          os.remove(T1.replace('.gipl','.nii'))
          os.remove(T1_N3.replace('.gipl','.nii'))
          
       if (os.path.exists(T2_N3)==False):
          if (os.path.exists(T2.replace('.gipl','.nii'))==False):
             convCmd = TconvCmd.substitute(infile=T2,outfile=T2.replace('.gipl','.nii'))
             print convCmd
             os.system(convCmd)
          biascorrectCmd = TbiascorrectCmd.substitute(infile=T2.replace('.gipl','.nii'),outfile=T2_N3.replace('.gipl','.nii'))
          print biascorrectCmd
          os.system(biascorrectCmd)
          convCmd = TconvCmd.substitute(infile=T2_N3.replace('.gipl','.nii'),outfile=T2_N3)
          print convCmd
          os.system(convCmd)
          os.remove(T2.replace('.gipl','.nii'))
          os.remove(T2_N3.replace('.gipl','.nii'))
       
       # Register T2 to T1
       T2RregT1  = T2_N3.replace('.gipl','_RregT1.gipl')
       dofoutRreg = T2RregT1.replace('.gipl','.dof');
       if (os.path.exists(dofoutRreg) == False):
          rregCmd = TrregCmd.substitute(tar = T1_N3, sou = T2_N3) + ' -dofout ' + dofoutRreg + ' -parin ' +  parfile + ' -Tp 5';
          os.system(rregCmd)
          transformCmd = TtransformCmd.substitute(sou = T2_N3, out = T2RregT1, dofin = dofoutRreg) + ' -target ' + T1_N3 + ' -cspline';
          os.system(transformCmd)
       
       # Fundamental parameters
       TISSUE_SEG_DIR = os.path.join(sMRI_DIR,'Tissue_Seg_ABC')
       
       if(os.path.exists(TISSUE_SEG_DIR)==False):
          os.mkdir(TISSUE_SEG_DIR)

       for file in os.listdir(TISSUE_SEG_DIR):
          if (fnmatch.fnmatch(file,'*.gz')):
               cmd = 'gunzip '+os.path.join(TISSUE_SEG_DIR,file)
               print cmd
               os.system(cmd)
       
       regtar = 'T1_N3';
       EMSreg = 0
       SUFFIX = 'ABC'
       print SUFFIX
       EMSfile  = os.path.join(TISSUE_SEG_DIR,(SUFFIX+'param.xml')); 
       Aregfile  = os.path.join(TISSUE_SEG_DIR,('PreAreg_'+SUFFIX+'.xml')); 
       if (EMSreg == 0):
         # trick to disable warping in EMS
         # cp the transformation file with identity trans to the tmp folder

#          EMST1warp_tar = EMST1warp_orig.replace((ORIG_DATA_DIR+'processing'),TISSUE_SEG_DIR).replace('T1name',prefix+'_'+dir_tag+'_T1_050505mm_RAI_N3corrected').replace('EMSinfo',SUFFIX);
#          EMST2warp_tar = EMST2warp_orig.replace((ORIG_DATA_DIR+'processing'),TISSUE_SEG_DIR).replace('T1name',prefix+'_'+dir_tag+  '_T1_050505mm_RAI_N3corrected').replace('T2name',prefix+'_'+dir_tag+  '_T2_050510mm_RAI_N3corrected_RregT1').replace('EMSinfo',SUFFIX);
#          os.system('cp '+ EMST1warp_orig + ' ' + EMST1warp_tar);
#          os.system('cp '+ EMST2warp_orig + ' ' + EMST2warp_tar);

         # 1 - 1. affinely align atlas to the subject and make subject specific atlas
         newTemplate = atlasFile.replace(atlasLoc,TISSUE_SEG_DIR).replace('.gipl.gz','.gipl');
         dof = newTemplate.replace('.gipl','_areg.dof');

         fareg = open(Aregfile,'a');
         if (os.path.exists(dof) == False) : 
            rregCmd = TrregCmd.substitute(tar = eval(regtar), sou = atlasFile)+' -dofout '+dof+' -parin '+parfile+' -Tp 5';
            os.system(rregCmd);
            fareg.write(rregCmd+'\n'+'\n');
            aregCmd = TaregCmd.substitute(tar = eval(regtar), sou = atlasFile) + ' -dofin ' + dof + ' -dofout ' +  dof + ' -parin ' +  parfile + ' -Tp 5 -p9';
            os.system(aregCmd);
            fareg.write(aregCmd+'\n'+'\n');
         else:
            print 'Affine alignement of the atlas to '+ regtar+'  already done'
			   
         # 1 - 2. transform the template accordingly
         id = 0;  #id used for abc
         for parc in ['template','white','gray','csf','rest']:
            #segmentation files used in ems and abc
            ems_parc = os.path.join(TISSUE_SEG_DIR,parc+'.gipl')
            if(id>0):
               abc_parc = os.path.join(TISSUE_SEG_DIR,str(id)+'.mha')
            else:
               abc_parc = os.path.join(TISSUE_SEG_DIR,parc+'.mha')
            if (os.path.exists(ems_parc)==False):
                # gunzip the gipl.gz
                if (fnmatch.fnmatch(newTemplate.replace('template.gipl',parc+'.gipl'),'*.gz')):
                   gunzipCmd = 'gunzip '+newTemplate.replace('template.gipl',parc+'.gipl')
                   os.system(gunzipCmd)
                else:
                   print 'Transforming'+parc+'.gipl'
                   transformCmd = TtransformCmd.substitute(sou = atlasFile.replace('template.gipl',parc+'.gipl'), out = ems_parc, dofin = dof) + ' -target ' + T1_N3 + ' -cspline';
                   os.system(transformCmd)
                   fareg.write(transformCmd+'\n'+'\n');
            
            if(os.path.exists(abc_parc)==False):
                  convCmd = TconvCmd.substitute(infile=ems_parc,outfile=abc_parc)
                  print convCmd
                  os.system(convCmd)
                  os.remove(ems_parc)
            id = id +1
         fareg.close();

         # 3. perform itkEMS-based segmentation
         # 3-1 create EMS file
         if (SUFFIX == 'EMS_v18'):
            EMS_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+TISSUE_SEG_DIR+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+TISSUE_SEG_DIR+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>GIPL</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+T1_N3+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+T2RregT1+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<FILTER-ITERATIONS>5</FILTER-ITERATIONS>\n\
<FILTER-TIME-STEP>0.01</FILTER-TIME-STEP>\n\
<FILTER-METHOD>Curvature flow</FILTER-METHOD>\n\
<MAX-BIAS-DEGREE>4</MAX-BIAS-DEGREE>\n\
<PRIOR-1>1</PRIOR-1>\n\
<PRIOR-2>0.5</PRIOR-2>\n\
<PRIOR-3>0.5</PRIOR-3>\n\
<PRIOR-4>0.1</PRIOR-4>\n\
<DO-ATLAS-WARP>0</DO-ATLAS-WARP>\n\
<ATLAS-WARP-GRID-X>5</ATLAS-WARP-GRID-X>\n\
<ATLAS-WARP-GRID-Y>5</ATLAS-WARP-GRID-Y>\n\
<ATLAS-WARP-GRID-Z>5</ATLAS-WARP-GRID-Z>\n\
</SEGMENTATION-PARAMETERS>\n'
         if SUFFIX == 'ABC':
            EMS_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+TISSUE_SEG_DIR+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+TISSUE_SEG_DIR+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>Nrrd</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+T1_N3+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+T2RregT1+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<FILTER-ITERATIONS>10</FILTER-ITERATIONS>\n\
<FILTER-TIME-STEP>0.01</FILTER-TIME-STEP>\n\
<FILTER-METHOD>Curvature flow</FILTER-METHOD>\n\
<MAX-BIAS-DEGREE>4</MAX-BIAS-DEGREE>\n\
<PRIOR>1.2</PRIOR>\n\
<PRIOR>1</PRIOR>\n\
<PRIOR>0.7</PRIOR>\n\
<PRIOR>1</PRIOR>\n\
<DO-ATLAS-WARP>0</DO-ATLAS-WARP>\n\
<ATLAS-WARP-FLUID-ITERATIONS>1</ATLAS-WARP-FLUID-ITERATIONS>\n\
\n\
<!-- Mapping types: default is affine, can be rigid or id instead -->\n\
<ATLAS-LINEAR-MAP-TYPE>id</ATLAS-LINEAR-MAP-TYPE>\n\
<IMAGE-LINEAR-MAP-TYPE>id</IMAGE-LINEAR-MAP-TYPE>\n\
\n\
</SEGMENTATION-PARAMETERS>\n'
                    
         fout = open(EMSfile,'w');
         fout.write(EMS_info);
         fout.close();

         if (os.path.exists(os.path.join(TISSUE_SEG_DIR,'*_ABC*.nrrd*')) == False):
              # 3-2 run ABC
              print ABCCmd + ' ' + EMSfile
              os.system(ABCCmd + ' ' + EMSfile)

              # 3-4 reduce intensity space from 0...32k to 0..1024
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*_corrected_EMS.nrrd*'):
                      ImageMathCmd = TImageMathCmd.substitute(infile = image, outfile = image) + '  -constOper 3,32'
                      os.system(ImageMathCmd)
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*_posterior*_EMS.nrrd*'):
                      ImageMathCmd = TImageMathCmd.substitute(infile = image, outfile = image) + '  -constOper 3,32'
                      os.system(ImageMathCmd)
         # 8. mask the brain
         # ---------------------------------------------------------------------
         # ---------------------------------------------------------------------
         # ---------------------------------------------------------------------
         T1_ABC = T1_N3.replace(sMRI_DIR,TISSUE_SEG_DIR).replace('_RAI','_ABCStripped')
         T2_ABC = T2RregT1.replace(sMRI_DIR,TISSUE_SEG_DIR).replace('_RAI','_ABCStripped');
         brainmask = os.path.join(TISSUE_SEG_DIR,'ABC_brainMask.gipl')
         print 'Doing Skull Stripping'
         print os.listdir(TISSUE_SEG_DIR)
         for img in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*labels_'+SUFFIX+'.nrrd'):
            print img
            brainmaskIn = os.path.join(TISSUE_SEG_DIR,img);

         print 'Creating Brain Mask'
         os.system('SegPostProcess ' + brainmaskIn + ' -o ' + brainmask + ' -v');

         if (os.path.exists(T1_ABC)==False):
            print 'Stripping T1'
            ImageMathCmd = TImageMathCmd.substitute(infile = T1_N3, outfile = T1_ABC) + ' -mask ' + brainmask
            print ImageMathCmd
            os.system(ImageMathCmd)
			   
         if (os.path.exists(T2_ABC)==False):
            print 'Stripping T2'
            ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2_ABC) + ' -mask ' + brainmask
            print ImageMathCmd
            os.system(ImageMathCmd)

         #gzip all the gipls
         for file in os.listdir(sMRI_DIR):
            if (fnmatch.fnmatch(file,'*.gipl')):
               cmd = 'gzip '+os.path.join(sMRI_DIR,file)
               print cmd
               os.system(cmd)
         for file in os.listdir(TISSUE_SEG_DIR):
            if (fnmatch.fnmatch(file,'*.gipl')):
               cmd = 'gzip '+os.path.join(TISSUE_SEG_DIR,file)
               print cmd
               os.system(cmd)

         os.system('rm '+os.path.join(TISSUE_SEG_DIR,'*.mha'))
         


