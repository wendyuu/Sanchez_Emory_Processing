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
   prefixfile = os.path.join(ORIG_DATA_DIR,'processing',options.filename)
   prefixlist = open(prefixfile,'r')
elif len(args) > 0:
   print 'Reading input from the terminal'
   prefixlist = args
   print args
else:
   print ('Input error: Either give a file name to read the prefix names of the subjects or type in from the terminal')

if options.dir_tag:
      dir_tag = options.dir_tag
      
# LOCATION VARIABLES for the atlas/template
NEOSEGT1warp_orig = os.path.join(ORIG_DATA_DIR,'processing/T1name_to_template_EMSinfo.affine')  
NEOSEGT2warp_orig = os.path.join(ORIG_DATA_DIR,'processing/T1name_to_T2name_EMSinfo.affine')
NEOSEGreg = 0
# SYSTEM VARIABLES
# usually DO NOT EDIT THESE
from string import Template
TatlasLoc = Template('/primate/SanchezEmory/BrainDevYerkes/sMRIatlas/${age}/T2/Areg2template/all_subjects/sAtlas')
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
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -i $infile -o $outfile')

#neoseg
NEOSEGCmd = '/tools/bin_linux64/neoseg_1.7'
#recompute montage pictures?
recomputeMontage = 1

# the txt file that stores all the prefix names
parfile = os.path.join(ORIG_DATA_DIR ,'processing/Reg_par_NMI.txt')
# loop through the folders to calculate tensor
for prefix in prefixlist:
    prefix = prefix[0:5]
    SUBJ_DIR =  os.path.join(ORIG_DATA_DIR,prefix,dir_tag)
    atlasLoc = TatlasLoc.substitute(age=dir_tag)
    atlasFile = os.path.join(atlasLoc,'templateT2.gipl.gz')
    if (os.path.exists(atlasFile)==False):
       os.system('gzip '+atlasFile.replace('.gipl.gz','.gipl'))
       
    print SUBJ_DIR
    if os.path.exists(SUBJ_DIR):
       
       sMRI_DIR = os.path.join(SUBJ_DIR,'sMRI')
       #gunzip everything
       for file in os.listdir(sMRI_DIR):
          if (fnmatch.fnmatch(file,'*gipl.gz')):
               cmd = 'gunzip '+os.path.join(sMRI_DIR,file)
               print cmd
               os.system(cmd)

       # generate first step nrrd files
       T1_temp = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T1.nrrd')
       T1_nrrd = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T1_050505mm.nhdr')
       if (os.path.exists(T1_nrrd)==False):
          unugzipCmd = TunugzipCmd.substitute(infile=T1_temp,outfile=T1_nrrd)
          print unugzipCmd
          os.system(unugzipCmd)
       T2_temp = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T2.nrrd')
       T2_nrrd = os.path.join(sMRI_DIR,prefix+'_'+dir_tag+'_T2_050510mm.nhdr')
       if (os.path.exists(T2_nrrd)==False):
          unugzipCmd = TunugzipCmd.substitute(infile=T2_temp,outfile=T2_nrrd)
          print unugzipCmd
          os.system(unugzipCmd)
       
       # Procedure
       # A) Bias field correction
       # B) Use NEOSEG to do tissue segmentation
              #1) Register to the new atlas
              #2) Curve Smoothing
              #3) Init using rview manually
              #4) RunNEOSEG
       # C) Warping etc

       # T1 and T2 RAI gipls
       T1_gipl = T1_nrrd.replace('.nhdr','.gipl')
       T2_gipl = T2_nrrd.replace('.nhdr','.gipl')
       if (os.path.exists(T1_gipl)==False):
          convCmd = TconvCmd.substitute(infile=T1_nrrd,outfile=T1_gipl)
          print convCmd
          os.system(convCmd)
       if (os.path.exists(T2_gipl)==False):
          convCmd = TconvCmd.substitute(infile=T2_nrrd,outfile=T2_gipl)
          print convCmd
          os.system(convCmd)

       T1 = T1_gipl.replace('.gipl','_RAI.gipl')
       T1_N3 = T1.replace('.gipl','_N3corrected.gipl')
       T2  = T2_gipl.replace('.gipl','_RAI.gipl')
       T2_N3 = T2.replace('.gipl','_N3corrected.gipl')
       
       if (os.path.exists(T1)==False):
          reorientCmd = TreorientCmd.substitute(infile = T1_gipl,outfile = T1)
          print reorientCmd + '-setorient LAI-RAI'
          os.system(reorientCmd + '-setorient LAI-RAI')
       if (os.path.exists(T1_gipl)):
          os.remove(T1_gipl)
          
       if (os.path.exists(T2)==False):
          reorientCmd = TreorientCmd.substitute(infile = T2_gipl,outfile = T2)
          print reorientCmd + '-setorient LAI-RAI'
          os.system(reorientCmd + '-setorient LAI-RAI')
       if (os.path.exists(T2_gipl)):
          os.remove(T2_gipl)
          
                                                                       
       # Bias field correction
       #2) Apply the mri_nu_correct
       if (os.path.exists(T1_N3)==False):
          if(os.path.exists(T1_N3+'.gz')):
             gunzip + ' '+T1_N3+'.gz'
          else:
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
          if(os.path.exists(T2_N3+'.gz')):
             gunzip + ' '+T2_N3+'.gz'
          else:
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
       dofoutRreg = T2RregT1.replace('.gipl','.dof')
       if (os.path.exists(dofoutRreg) == False):
          rregCmd = TrregCmd.substitute(tar = T1_N3, sou = T2_N3) + ' -dofout ' + dofoutRreg + ' -parin ' +  parfile + ' -Tp 5'
          os.system(rregCmd)
          transformCmd = TtransformCmd.substitute(sou = T2_N3, out = T2RregT1, dofin = dofoutRreg) + ' -target ' + T1_N3 + ' -cspline'
          os.system(transformCmd)
       
       # Fundamental parameters
       TISSUE_SEG_DIR = os.path.join(sMRI_DIR,'Tissue_Seg_Neoseg')
       
       if(os.path.exists(TISSUE_SEG_DIR)==False):
          os.mkdir(TISSUE_SEG_DIR)

       for file in os.listdir(TISSUE_SEG_DIR):
          if (fnmatch.fnmatch(file,'*.gz')):
               cmd = 'gunzip '+os.path.join(TISSUE_SEG_DIR,file)
               print cmd
               os.system(cmd)
       
       regtar = 'T2RregT1'
       SUFFIX = 'NEOSEG'
       print SUFFIX
       NEOSEGfile  = os.path.join(TISSUE_SEG_DIR,(SUFFIX+'param.xml')) 
       Aregfile  = os.path.join(TISSUE_SEG_DIR,('PreAreg_'+SUFFIX+'.xml')) 
       if (NEOSEGreg == 0):
         # trick to disable warping in NEOSEG
         # cp the transformation file with identity trans to the tmp folder

         NEOSEGT1warp_tar = NEOSEGT1warp_orig.replace((ORIG_DATA_DIR+'processing'),TISSUE_SEG_DIR).replace('T1name',prefix+'_'+dir_tag+'_T2_050510mm_RAI_N3corrected_RregT1').replace('EMSinfo',SUFFIX).replace('template','templateT2')
         NEOSEGT2warp_tar = NEOSEGT2warp_orig.replace((ORIG_DATA_DIR+'processing'),TISSUE_SEG_DIR).replace('T1name',prefix+'_'+dir_tag+  '_T2_050510mm_RAI_N3corrected_RregT1').replace('T2name',prefix+'_'+dir_tag+  '_T1_050505mm_RAI_N3corrected').replace('EMSinfo',SUFFIX)
         os.system('cp '+ NEOSEGT1warp_orig + ' ' + NEOSEGT1warp_tar)
         os.system('cp '+ NEOSEGT2warp_orig + ' ' + NEOSEGT2warp_tar)

         # 1 - 1. affinely align atlas to the subject and make subject specific atlas
         newTemplate = atlasFile.replace(atlasLoc,TISSUE_SEG_DIR).replace('.gipl.gz','.gipl')
         dof = newTemplate.replace('.gipl','_areg.dof')

         fareg = open(Aregfile,'a')
         if (os.path.exists(dof) == False) : 
            rregCmd = TrregCmd.substitute(tar = eval(regtar), sou = atlasFile)+' -dofout '+dof+' -parin '+parfile+' -Tp 5'
            os.system(rregCmd)
            fareg.write(rregCmd+'\n'+'\n')
            aregCmd = TaregCmd.substitute(tar = eval(regtar), sou = atlasFile) + ' -dofin ' + dof + ' -dofout ' +  dof + ' -parin ' +  parfile + ' -Tp 5 -p9'
            os.system(aregCmd)
            fareg.write(aregCmd+'\n'+'\n')
         else:
            print 'Affine alignement of the atlas to '+ regtar+'  already done'
			   
         # 1 - 2. transform the template accordingly

         for parc in ['templateT2','white','gray','csf','rest']:
            ems_parc = os.path.join(TISSUE_SEG_DIR,parc+'.gipl')
            if (os.path.exists(ems_parc)==False):
                # gunzip the gipl.gz
                if (fnmatch.fnmatch(newTemplate.replace('templateT2.gipl',parc+'.gipl'),'*.gz')):
                   gunzipCmd = 'gunzip '+newTemplate.replace('templateT2.gipl',parc+'.gipl')
                   os.system(gunzipCmd)
                else:
                   print 'Transforming'+parc+'.gipl'
                   transformCmd = TtransformCmd.substitute(sou = atlasFile.replace('templateT2.gipl',parc+'.gipl'), out = ems_parc, dofin = dof) + ' -target ' + T1_N3 + ' -cspline'
                   os.system(transformCmd)
                   fareg.write(transformCmd+'\n'+'\n')
         fareg.close()


         # 2. edit pixdims for all images in TISSUE_SEG_DIR
         # 2-1 Get the original pixel information
         origPixdim = os.popen('ImageStat '+T1_N3+' -info | grep Pixdims').read()
         origdim = os.popen('ImageStat '+T1_N3+' -info | grep Dims').read()
         origPixdims = str(origPixdim).split(' ')
         origdims = str(origdim).split(' ')

         # 2-2 Change pixdim to 1.0*1.0*1.0				
         giplpattern = '*.gipl*'
         for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),giplpattern):
              ImageMathCmd = TImageMathCmd.substitute(infile = os.path.join(TISSUE_SEG_DIR,image), outfile = os.path.join(TISSUE_SEG_DIR,image)) + ' -editPixdims 1.0,1.0,1.0'
              os.system(ImageMathCmd)
         ImageMathCmd = TImageMathCmd.substitute(infile = T1_N3, outfile = T1_N3) + ' -editPixdims 1.0,1.0,1.0'
         os.system(ImageMathCmd)
         ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2RregT1) + ' -editPixdims 1.0,1.0,1.0'
         os.system(ImageMathCmd)
         # change the origins in the registration accordingly
         for dim in [1,2,3]:
              for sub in ['sou','tar']:
                      tag = (sub+str(dim)).capitalize()
                      cons = 1.0*float(origdims[dim])
                      #for filetag in ['T1','T2']:
                              #warpname = eval('NEOSEG'+filetag+'warp_tar')
                              #os.system('text_subst.pl ' + tag + ' ' +str(cons) +' ' +warpname)	
         # 3. perform itkNEOSEG-based segmentation
         # 3-1 create NEOSEG file
         NEOSEG_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+TISSUE_SEG_DIR+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+TISSUE_SEG_DIR+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>GIPL</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+T2RregT1+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+T1_N3+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<FILTER-ITERATIONS>10</FILTER-ITERATIONS>\n\
<FILTER-TIME-STEP>0.01</FILTER-TIME-STEP>\n\
<FILTER-METHOD>Curvature flow</FILTER-METHOD>\n\
<MAX-BIAS-DEGREE>1</MAX-BIAS-DEGREE>\n\
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

         if (os.path.exists(os.path.join(TISSUE_SEG_DIR,'*_Neoseg*.gipl*')) == False or options.NEOSEG == True):
              # 3-2 run neoseg
              print NEOSEGCmd + ' ' + NEOSEGfile
              os.system(NEOSEGCmd + ' ' + NEOSEGfile)

              # 3-4 reduce intensity space from 0...32k to 0..1024
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*_corrected_NEOSEG.gipl*'):
                      ImageMathCmd = TImageMathCmd.substitute(infile = image, outfile = image) + '  -constOper 3,32'
                      os.system(ImageMathCmd)
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*_posterior*_NEOSEG.gipl*'):
                      ImageMathCmd = TImageMathCmd.substitute(infile = image, outfile = image) + '  -constOper 3,32'
                      os.system(ImageMathCmd)

              # 3-5 edit back the pixel size
              for image in fnmatch.filter(os.listdir(TISSUE_SEG_DIR),giplpattern):
                 ImageMathCmd = TImageMathCmd.substitute(infile = os.path.join(TISSUE_SEG_DIR,image), outfile = os.path.join(TISSUE_SEG_DIR,image)) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
                 os.system(ImageMathCmd)                                        
              ImageMathCmd = TImageMathCmd.substitute(infile = T1_N3, outfile = T1_N3) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
              os.system(ImageMathCmd)
              ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2RregT1) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
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
