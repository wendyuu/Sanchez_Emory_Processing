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
ORIG_PROCESSING_DIR = os.path.join(ORIG_DATA_DIR,'Sanchez_Emory_Processing')
ORIG_STATS_DIR = os.path.join(ORIG_DATA_DIR,'STATS')
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
   prefixfile = os.path.join(ORIG_PROCESSING_DIR,options.filename);
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
TatlasLoc = Template('/primate/SanchezEmory/BrainDevYerkes/sMRIatlas/${age}/T1/Areg2template/all_subjects/sAtlas/ABC') #new atlas built with Emory data
atlasLoc = ('/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/ABC_stripped/') #old atlas from CoeMonkey data
rigidatlas = '/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template.gipl'
atlasEMS = '/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/template_hardseg.gipl'
#BRAINS registration
BRAINSFitCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/BRAINSFit --movingVolume $sou --fixedVolume $tar --outputTransform $trans')) 
TResampleCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/ResampleVolume2 $sou $out -i bs -n 4 -R $ref -f $trans'))

#rview registration
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TrregCmd = Template('/tools/rview_linux64_2008/rreg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
# the txt file that stores all the prefix names
parfile = os.path.join(ORIG_PROCESSING_DIR ,'Reg_par_NMI_Bspline.txt')

TintensityRescaleCmd = Template('/tools/bin_linux64/IntensityRescaler')
TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
TbiascorrectCmd = Template(os.path.join(SlicerLoc,'lib/Slicer3/Plugins/N4ITKBiasFieldCorrection --inputimage $infile --outputimage $outfile'))
TunugzipCmd = Template(os.path.join(SlicerLoc,'bin/unu')+' save -f nrrd -e gzip -i $infile -o $outfile')
TunuClampCmd = Template(os.path.join(SlicerLoc,'bin/unu')+' 3op clamp $min  $infile $max -o $outfile')
TChangeOrigin = Template(os.path.join(ORIG_PROCESSING_DIR,'ChangeOrigin.py $file $file'))
ImageStatCmd = ('/tools/bin_linux64/ImageStat')
ABCCmd = '/tools/bin_linux64/ABC' #ABC

#Volume stats files
ABCVOL = os.path.join(ORIG_STATS_DIR,age+'_ABC_vol.txt')
VOLSTATS = 'CASE\tBACKGROUND\tWM\tGM\tCSF'



############################PIPELINE##############################################################
############################1. N4 CORRECTION######################################################
############################2. RIGID REGISTRATION (T1->ATLAS; T2->T1)#############################
############################3. ABC################################################################
############################4. INTENSITY RESCALING################################################
############################5. CALCULATE THE VOLUMES OF EMS SEGMENTED AREAS

# loop through the folders to calculate tensor
for prefix in prefixlist:
    prefix = prefix[0:5]
    SUBJ_DIR =  os.path.join(ORIG_DATA_DIR,prefix,age)

    if(options.newatlas == True): #Use new atlas
       if os.path.exists(TatlasLoc.substitute(age=age)) == False:
          print 'NEW ATLAS DOESN\'T EXIST, USING OLD ATLAS'
       else:
          atlasLoc = TatlasLoc.substitute(age=age)
    else:
       pass
    
    #For each subject
    if os.path.exists(SUBJ_DIR):
       sMRI_DIR = os.path.join(SUBJ_DIR,'sMRI')
       TISSUE_SEG_DIR = os.path.join(sMRI_DIR,'Tissue_Seg_ABC')
       if(os.path.exists(TISSUE_SEG_DIR)==False):
          os.mkdir(TISSUE_SEG_DIR)
       
       #log file of all the commands
       log_file = os.path.join(sMRI_DIR,'log_ABCSEG.txt')
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
             #print unugzipCmd
             #os.system(unugzipCmd)
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
       BFitCmd = BRAINSFitCmd.substitute(tar = rigidatlas, sou = T1_N4, trans = T1TransRreg) + ' --transformType Rigid --useCenterOfHeadAlign --outputVolumePixelType short'
       log = log + BFitCmd + '\n\n'
       ResampleCmd = TResampleCmd.substitute(sou =T1_N4, out = T1RregAtlas, ref = rigidatlas,trans=T1TransRreg)+' -t rt'
       log = log + ResampleCmd + '\n\n'
       clampCmd = TunuClampCmd.substitute(infile = T1RregAtlas, outfile = T1RregAtlas, min = 0, max = 1000000)
       log = log + clampCmd + '\n\n'
       if (os.path.exists(T1TransRreg) == False):
          print BFitCmd
          os.system(BFitCmd)
          print ResampleCmd
          os.system(ResampleCmd)
          #Get rid of the negative parts
          print clampCmd
          os.system(clampCmd)

       #register T2 to atlas-registered T1
       BFitCmd = BRAINSFitCmd.substitute(tar = T1RregAtlas, sou = T2_N4, trans = T2TransRreg) + ' --transformType Rigid --interpolationMode BSpline --outputVolumePixelType short --initialTransform ' + T1TransRreg
       log = log + BFitCmd + '\n\n'
       ResampleCmd = TResampleCmd.substitute(sou =T2_N4, out = T2RregT1, ref = rigidatlas,trans=T2TransRreg)+' -t rt'
       log = log + ResampleCmd + '\n\n'
       clampCmd = TunuClampCmd.substitute(infile = T2RregT1, outfile = T2RregT1, min = 0, max = 1000000)
       log = log + clampCmd + '\n\n'
       if (os.path.exists(T2TransRreg) == False):
          print BFitCmd
          os.system(BFitCmd)
          print ResampleCmd
          os.system(ResampleCmd)
          #Get rid of the negative parts
          print clampCmd
          os.system(clampCmd)
       
       ################################
       #3. ABC
       ################################
       T1_ABC = T1RregAtlas.replace(Rreg2atlas_DIR,TISSUE_SEG_DIR).replace('.nrrd','_ABCStripped.nrrd')
       T1_ABCini = T1RregAtlas.replace(Rreg2atlas_DIR,TISSUE_SEG_DIR).replace('.nrrd','_iniStripped.nrrd')
       T2_ABC = T2RregT1.replace(Rreg2atlas_DIR,TISSUE_SEG_DIR).replace('.nrrd','_ABCStripped.nrrd')
       T2_ABCini = T2RregT1.replace(Rreg2atlas_DIR,TISSUE_SEG_DIR).replace('.nrrd','_iniStripped.nrrd')
       
       brainmask = os.path.join(TISSUE_SEG_DIR,'ABC_brainMask.nrrd')
       
       if (os.path.exists(T1_ABC) == False or os.path.exists(T2_ABC) == False):
          for SUFFIX in ['ABCini','ABC']:
             if(SUFFIX == 'ABCini'):
                #initial stull stripping
                infile1 = T2RregT1
                infile2 = T1RregAtlas
                outfile1 = eval('T2_'+SUFFIX)
                outfile2 = eval('T1_'+SUFFIX)
             else:
                infile1 = T1_ABCini
                infile2 = T2_ABCini
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
<DO-ATLAS-WARP>1</DO-ATLAS-WARP>\n\
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

          #clean up
          rmcmd = 'rm '+ os.path.join(TISSUE_SEG_DIR,'*posterior*')
          log = log + rmcmd + '\n\n'
          print rmcmd
          os.system(rmcmd)

       #####################################################################
       #######################4. Intensity Calibration
       #####################################################################
       sourceEMSimg = os.path.join(TISSUE_SEG_DIR,fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*labels_ABC.nrrd')[0])
       IntensityCal_info = '''# Target image: One image which is the reference
Target=%s

# Target segmentation image: EM Segmentation of the target image
TargetEMS=%s

# Source image(s): Image(s) to be intensity rescaled base on reference image
# Source segmentation image(s): EM Segmentation image(s)
Source=%s
SourceEMS=%s
Source=%s
SourceEMS=%s

# Label List: Usually 1,2 and 3 are the labels for White, Gray and CSF pattern
Label=1
Label=2
Label=3

# Target instensity windowing: Do you want to adjust min/max intensity of the target ? [ON/OFF]
TargetWindowing=ON

# Source instensity windowing: Do you want to adjust min/max intensity of source image(s) ? [ON/OFF]
SourceWindowing=ON

# Class matching: Do you want to iteratively adjust classes ? [ON/OFF]
ClassMatching=ON

# Sigma for class matching: Standard deviation for min/max adjustment
Sigma=3

# OutputSuffix: Suffix for output filename
OutputSuffix=-irescaled

# OutputDir: Output Directory (Not necessary)
# OutputDir=%s

# Intensity rescaler script end'''%(rigidatlas,atlasEMS,T1_ABC,sourceEMSimg,T2_ABC,sourceEMSimg,TISSUE_SEG_DIR)
       
       IntensityCal_file = os.path.join(TISSUE_SEG_DIR,'IntensityRescalar.txt')
       f = open(IntensityCal_file,'w')
       f.write(IntensityCal_info)
       f.close()
       cmd = 'IntensityRescaler  -input '+IntensityCal_file +' -v'
       log = log + cmd + '\n\n'
       if(os.path.exists(T1_ABC.replace('.nrrd','-irescaled.nrrd')) == False or os.path.exists(T2_ABC.replace('.nrrd','-irescaled.nrrd')) == False):
          print cmd
          os.system(cmd)

       
       #4. Calculate the volumes of segmented ares after ABC
       ABC_label = os.path.join(TISSUE_SEG_DIR,fnmatch.filter(os.listdir(TISSUE_SEG_DIR),'*labels_ABC.nrrd')[0])
       ABC_vol = ABC_label.replace('.nrrd','_vol.txt')
       cmd = ImageStatCmd + ' ' + ABC_label +' -histo'
       log = log + cmd + '\n\n'
       if (os.path.exists(ABC_vol) == False):
          print 'Computing ABC volumes'
          print cmd
          os.system(cmd)
       print prefix
       ind_volstats = fnmatch.filter(open(ABC_vol,'r').readlines(),'*volumes =*')[0]
       VOLSTATS = VOLSTATS+'\n'+ind_volstats.replace('volumes = ','').replace('{','').replace('},','').replace('}','').replace(';\n','').replace('0,',prefix+'\t').replace('1,','\t').replace('2,','\t').replace('3,','\t')

       #5. Doing warping
       #Doing warping subcortical structures

set allcases = $ORIG_DATA_DIR/${SUBJ_DIR_PREFIX}???/sMRI/WarpROI/*_warp.hfield.gz
set numcases = $#allcases
set randnum  = `randperm 1 $numcases`
foreach index ($randnum)          
    set case = $allcases[$index] 
    set caseID = $case:h:h:h:t

    set targetDir = $case:h:h/WarpSubCort
    if (! -e $targetDir) mkdir $targetDir

    set source = $atlasSubCortFile
    set targetAff = $targetDir/$caseID:t_AffSubCort.gipl.gz
    set targetWarp = $targetDir/$caseID:t_AffWarpSubCort.gipl.gz
    set dofAreg = $case:h/template_areg_$caseID.dof

    if (! -e $targetWarp || ! -e $targetAff) then
	echo warping subcortical segementation $targetWarp
        set targetWarp = $targetWarp:r
        set targetAff = $targetAff:r

	gunzip -c $case >! $case:r
	set case = $case:r

	# nearest neighbor interpolation warping
	$transformCmd $source $targetAff -dofin $dofAreg
        $warpCmd -a $targetAff $case $targetWarp -nearest

	gzip -f $targetWarp $targetAff 
	rm $case 
    endif
end


# compute  volumes 
set allcases = $ORIG_DATA_DIR/${SUBJ_DIR_PREFIX}???/sMRI/WarpSubCort/*WarpSubCort.gipl.gz
set numcases = $#allcases
set randnum  = `randperm 1 $numcases`
foreach index ($randnum)          
    set case = $allcases[$index] 
    set caseID = $case:h:h:h:t

    set target = $case:r:r_vol.txt
    if (! -e $target ) then
	echo computing subcortical structure volume $target
	ImageStat $case -histo
    endif
end

set areaFile = $curpath/SubCort_vol.txt
if (-e $areaFile) rm $areaFile
echo ID_number >! $areaFile
cat $atlasSubCortHeaderFile >> $areaFile
text_subst.pl 'ID_number\n' 'ID_number '  $areaFile >> /dev/null
foreach histoFile ($ORIG_DATA_DIR/${SUBJ_DIR_PREFIX}???/sMRI/WarpSubCort/*WarpSubCort_vol.txt )
    echo $histoFile:t:s/_prob//:s/_vol.txt// >> $areaFile 
    grep volumes $histoFile >> $areaFile
end
remove_Commas_Brackets $areaFile >> /dev/null
text_subst.pl '\nvolumes = 0 ' ' '  $areaFile >> /dev/null
text_subst.pl '_AffWarpSubCort' ' '  $areaFile >> /dev/null
text_subst.pl ';' ''  $areaFile >> /dev/null
foreach i ( 1 2 3 4 5 6 7 8 9 10 )
   text_subst.pl " $i " " "  $areaFile >> /dev/null
end

       #write log file of all the commands
       f = open(log_file,'w')
       f.write(log)

       
f = open(ABCVOL,'w')
f.write(VOLSTATS)
         


