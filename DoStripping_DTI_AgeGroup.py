#! /usr/bin/env python

# Script to do skull stripping on DTI images
# 1) Use ABC of iDWI/b0 as dual channels
# 2) Register T2 to FA and use the accordingly-transformed T2 brain mask for stripping
#
# Yundi Shi

import os
import fnmatch
import glob
from optparse import OptionParser

print 'Usage: \n\
DoStripping_DTI_AgeGroup.py [prefixlist] \n\
--file [-f] prefix_file \n\
--age [-a] age\n'


# VARIABLES SPECIFIC TO DATASET
ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
ORIG_PROCESSING_DIR = os.path.join(ORIG_DATA_DIR,'Sanchez_Emory_Processing')
grid_template = os.path.join(ORIG_DATA_DIR,'DTITemplate_CoeMonkeyFlu/grid_template.gipl.gz')

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
	prefixfile = os.path.join(ORIG_PROCESSING_DIR,options.filename);
	prefixlist_f = open(prefixfile,'r');
	prefixlist=prefixlist_f.readlines();
	prefixlist_f.close()
elif len(args) > 0:
	print 'Reading input from the terminal'
	prefixlist = args;
else:
        print ('Input error: Either give a file name to read the prefix names of the subjects or type in from the terminal')

if options.dir_tag:
   dir_tag = options.dir_tag


# SYSTEM VARIABLES
from string import Template
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TAregCmd = Template('/tools/rview_linux64_2008/Areg $tar $sou')
TclampCmd = Template('/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64//bin/unu 3op clamp $min $infile $max -o $infile')
TupsampleCmd = Template('/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64//bin/unu resample -i $sou -o $out -s $dim -k hann:15')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TintensityRescaleCmd = Template('/tools/bin_linux64/IntensityRescaler')
TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TwarpCmd = Template('/tools/bin_linux64/fWarp')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
ThistmatchCmd = Template('/tools/bin_linux64/ImageMath $sou -matchHistogram $tar -outfile $out')
TunusaveCmd = Template('/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64//bin/unu save -f nrrd -i $infile -o $outfile')
<<<<<<< HEAD:DoStripping_DTI_AgeGroup.py
TChangeSpaceDir = Template(os.path.join(ORIG_PROCESSING_DIR,'ChangeSpaceDir.py $infile $outfile'))
=======
TChangeSpaceDir = Template('/primate/SanchezEmory/BrainDevYerkes/processing/ChangeSpaceDir.py $infile $outfile')
>>>>>>> 453825757c0cb34fea37c5e5899583fe84edc35e:DoStripping_DTI_AgeGroup.py
TSegPostProcess = Template('/tools/bin_linux64/SegPostProcess $infile -skullstripping $strippingfile -o $outfile -mask $BM')

#command and dir
ABCCmd = '/tools/bin_linux64/ABC'
ATLAS_DIR = '/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI/ABC_stripped/'
unuhead = '/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64//bin/unu head '
<<<<<<< HEAD:DoStripping_DTI_AgeGroup.py
parfile = os.path.join(ORIG_PROCESSING_DIR,'Reg_par_CC.txt')
parfile_bsp = os.path.join(ORIG_PROCESSING_DIR,'Reg_par_CC_Bspline.txt')
=======
parfile = os.path.join(ORIG_DATA_DIR,'Sanchez_Emory_Processing','Reg_par_CC.txt')
parfile_bsp = os.path.join(ORIG_DATA_DIR,'Sanchez_Emory_Processing','Reg_par_CC_Bspline.txt')
>>>>>>> 453825757c0cb34fea37c5e5899583fe84edc35e:DoStripping_DTI_AgeGroup.py
redo = 1
tag_template_exist = 0

# loop through the folders to calculate tensor
for line in prefixlist:
	prefix = line[0:5]
	#if 2weeks exists
	subjDir =  os.path.join(ORIG_DATA_DIR,prefix,dir_tag)
	DTIDir = os.path.join(subjDir,'DTI')
	if os.path.exists(DTIDir):
		f_log = open(os.path.join(DTIDir,'SkullStrippingLog.txt'),'w')
		#log files for all the commands
		log = ''
	       	###############VARIABLES#################		
		sMRIDir = os.path.join(subjDir,'sMRI')
		scale = 2
		#pixel dim to upsample the volumes to
		# save nhdr to nrrd in gzip
		print DTIDir
		print prefix
		print dir_tag
		if(fnmatch.filter(os.listdir(DTIDir),prefix+'_'+dir_tag+'_30dir_10DWI_*addB0.nhdr')):
			nhdr = os.path.join(DTIDir,fnmatch.filter(os.listdir(DTIDir),prefix+'_'+dir_tag+'_30dir_10DWI_*addB0.nhdr')[0])
			DWI = nhdr.replace('.nhdr','.nrrd')
			print 'Saving nhdr to nrrd in gzip'
			cmd = TunusaveCmd.substitute(infile=nhdr,outfile=DWI)+' -e gzip'		
			os.system(cmd)
			os.remove(nhdr)
		else:
			DWI = os.path.join(DTIDir,fnmatch.filter(os.listdir(DTIDir),prefix+'_'+dir_tag+'_30dir_10DWI_*addB0.nrrd')[0])
		raw = DWI.replace('.nrrd','.raw')
		rawgz = DWI.replace('.nrrd','.raw.gz')

		if(os.path.exists(raw)):  os.remove(raw)
		if(os.path.exists(rawgz)):  os.remove(rawgz)


		# calculate tensor
		B0 = DWI.replace(prefix+'_','B0'+'_'+prefix+'_')
		iDWI = DWI.replace(prefix+'_','iDWI'+'_'+prefix+'_')
		DTI = DWI.replace(prefix+'_','TENSOR'+'_'+prefix+'_')
		if(os.path.exists(B0)==False):
			dtiestim_cmd = 'dtiestim --dwi_image '+DWI+' --tensor_output '+DTI+' -m wls -t 20 --B0 '+B0 +' --idwi '+iDWI +' -v'
			print dtiestim_cmd
			os.system(dtiestim_cmd)

		# generating grid template for brain mask
		print 'Generating grid template '+grid_template+' for the brainmask'
		if(os.path.exists(grid_template)==False):
			upsampleCmd = TupsampleCmd.substitute(sou = B0, out = grid_template.replace('gipl.gz','nrrd'), dim=str(dim1*scale)+' '+str(dim2*scale)+' '+str(dim3*scale))
			print upsampleCmd
			os.system(upsampleCmd)
			convCmd = TconvCmd.substitute(infile=grid_template.replace('gipl.gz','nrrd'),outfile=grid_template)
			os.system(convCmd)
			os.system('rm '+grid_template.replace('gipl.gz','nrrd'))
			tag_template_exist=1
		
		nhdrContent = os.popen(unuhead+DWI).read()
		text_str_size = fnmatch.filter(nhdrContent.split('\n'),'sizes:*')[0]
		dim1 = int(text_str_size.split(' ')[1])
		dim2 = int(text_str_size.split(' ')[2])
		dim3 = int(text_str_size.split(' ')[3])
		
		#upsample the dwi
		DWI_up = DWI.replace('.nrrd','_upsampled.nrrd').replace('.nhdr','_upsampled.nhdr')
		DTI_up = DWI_up.replace(prefix+'_','TENSOR'+'_'+prefix+'_')
		print 'Calculating Tensor with the Brainmask'
		B0_up = DWI_up.replace(prefix+'_','B0'+'_'+prefix+'_')
		iDWI_up = DWI_up.replace(prefix+'_','iDWI'+'_'+prefix+'_')
		#upsample the DWIs using windowed sinc
		print 'upsample the DWIs using windowed sinc to '+str(dim1*scale)+'*'+str(dim2*scale)+'*'+str(dim3*scale)
		if(os.path.exists(DWI_up)==False):
		   upsampleCmd = TupsampleCmd.substitute(sou = DWI, out = DWI_up, dim=str(dim1*scale)+' '+str(dim2*scale)+' '+str(dim3*scale)+' =')
		   log = log + upsampleCmd + '\n'
		   print upsampleCmd
		   os.system(upsampleCmd)
		   # Get rid of negative values
		   cmd = TclampCmd.substitute(infile=DWI_up,min='0',max=str(10000000))
		   log = log + cmd + '\n'
		   print cmd
		   os.system(cmd)
		   # gzip the file
		   cmd = TunusaveCmd.substitute(infile=DWI_up,outfile=DWI_up)+' -e gzip'
		   log = log + cmd + '\n'
		   print cmd
		   os.system(cmd)
		else:
			pass

		ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=DWI_up,outfile=DWI_up)+' --dwi --noCenter'
		log = log + ChangeSpaceDirCmd + '\n'
		print ChangeSpaceDirCmd
		os.system(ChangeSpaceDirCmd)

		#Calculate the DTI for upsampled DWI
		if(os.path.exists(DTI_up)==False or redo == 1):
		   cmd = 'dtiestim --dwi_image '+DWI_up+' --tensor_output '+DTI_up+' -m wls --B0 '+B0_up +' --idwi '+ iDWI_up
		   log = log + cmd + '\n'
		   print cmd
		   os.system(cmd)

		#Using sMRI brain mask to do skull stripping
		sMRI_SSDir = os.path.join(sMRIDir,'Tissue_Seg_ABC')
<<<<<<< HEAD:DoStripping_DTI_AgeGroup.py
		Rreg2atlas_DIR = os.path.join(sMRI_DIR,'Rreg2Atlas')
=======
>>>>>>> 453825757c0cb34fea37c5e5899583fe84edc35e:DoStripping_DTI_AgeGroup.py
		T1 = os.path.join(sMRIDir,prefix + '_' + dir_tag +  '_T1_050505mm_RAI.gipl.gz')
		T2 = os.path.join(sMRIDir,prefix+'_'+dir_tag+'_T2_050510mm_RAI_N3corrected_RregT1.nhdr')
		sMRIbrainmask = os.path.join(sMRI_SSDir,'ABC_brainMask.gipl.gz')
		# Do simple thresholding using iDWI
		BM_DTI_wT2 = os.path.join(DTIDir,'brainMask_T2AregB0T105_upsampled.gipl.gz')
		printout = '##########Registering the b0 to T2 and using '+sMRIbrainmask+' for skull stripping#########'
		print printout
		log = log + printout + '\n'
		if(os.path.exists(BM_DTI_wT2)==False):
		   #########################################
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # 1) Reorient as images are NOT in RAI but RSP
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   B0_gipl = B0.replace('.nrrd','.gipl')  
		   if(os.path.exists(B0_gipl)==False):
			   printout = 'Change nrrd to gipl format'
			   log = log + printout + '\n'
			   convCmd = TconvCmd.substitute(infile=B0,outfile = B0_gipl)
			   os.system(convCmd)
		   B0_RAI_gipl = B0_gipl.replace('.gipl','_RAI.gipl.gz')
		   print B0_RAI_gipl
		   if (os.path.exists(B0_RAI_gipl)==False):
		        print 'Changing the orientation of B0 from LAI to RAI'
			#imconvert3 doesn't deal with .gz file
			reorientCmd = TreorientCmd.substitute(infile = B0_gipl,outfile = B0_RAI_gipl.replace('.gipl.gz','.gipl'))
			printout = reorientCmd  #for debugging
			log = log + printout + '\n'
			os.system(reorientCmd + '-setorient LAI-RAI')
			os.system('rm '+B0_gipl)
			os.system('gzip '+B0_RAI_gipl.replace('.gipl.gz','.gipl'))
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # B) Affine registration of T2 to B0 and transform the T1brainmask accordingly
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
	           # --------------------------------------------------------------------
	           dofoutAreg = B0_RAI_gipl.replace('.gipl.gz','T2Areg.dof')
		   # Registering T2 to B0 using bspline affine 
	           if(os.path.exists(dofoutAreg)==False):
			   aregCmd = TaregCmd.substitute(tar = B0_RAI_gipl, sou = T2) + ' -dofout ' + dofoutAreg + ' -parin ' +  parfile + ' -Tp 5'
			   printout = aregCmd
			   print printout
			   log = log + printout + '\n'
			   os.system(aregCmd)
			   aregCmd = TaregCmd.substitute(tar = B0_RAI_gipl, sou = T2) + ' -dofin ' + dofoutAreg + ' -dofout ' + dofoutAreg  + ' -parin ' +  parfile_bsp + ' -Tp 5'
			   printout = aregCmd
			   print printout
			   log = log + printout + '\n'
			   os.system(aregCmd)
		   # Transform the T2 brain mask accordingly
		   if(os.path.exists(BM_DTI_wT2)==False):
			   transformCmd = TtransformCmd.substitute(sou = sMRIbrainmask, out = BM_DTI_wT2, dofin = dofoutAreg) + ' -target ' + grid_template + ' -cspline'
			   os.system(transformCmd)
			   print 'Change the BM orientation back to the tensor space'
			   os.system('gunzip '+BM_DTI_wT2)
			   reorientCmd = TreorientCmd.substitute(infile = BM_DTI_wT2.replace('.gipl.gz','.gipl'),outfile = BM_DTI_wT2.replace('.gipl.gz','.gipl'))
			   print reorientCmd+' -setorient RAI-LAI'
			   os.system(reorientCmd + ' -setorient RAI-LAI')
			   os.system('gzip '+BM_DTI_wT2.replace('.gipl.gz','.gipl'))
                   #else:
		   # change the space dir, origin and measurement frame of the BM
		   ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=BM_DTI_wT2,outfile=BM_DTI_wT2)
		   printout = ChangeSpaceDirCmd
		   print printout
		   log = log + printout + '\n'
		   os.system(ChangeSpaceDirCmd)
		   
		# use b0 and idwi for tissue segmentation and skull stripping
		BM_DTI_b0idwi = os.path.join(DTIDir,'brainMask_wB0iDWI_upsampled.gipl.gz')
		printout = '\n\n\n##########Using ABC with B0 and iDWI for skull stripping##########'
		print printout
		log = log + printout + '\n'

		
		if(os.path.exists(BM_DTI_b0idwi) == False):
			#smooth iDWI
			cmd = TImageMathCmd.substitute(infile = iDWI_up,outfile = iDWI_up)+' -smooth -gauss -size 0.5'
			log = log + cmd + '\n'
			print cmd
			os.system(cmd)
		TISSUE_SEG_DIR = os.path.join(DTIDir,'ABCSeg_B0iDWI')
		if(os.path.exists(TISSUE_SEG_DIR)==False): os.mkdir(TISSUE_SEG_DIR)
		
		#generate xml file for abc
		ABC_xml = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>ABC</SUFFIX>\n\
<ATLAS-DIRECTORY>'+ATLAS_DIR+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+TISSUE_SEG_DIR+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>Nrrd</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+iDWI_up+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+B0_up+'</FILE>\n\
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
<ATLAS-LINEAR-MAP-TYPE>affine</ATLAS-LINEAR-MAP-TYPE>\n\
<IMAGE-LINEAR-MAP-TYPE>id</IMAGE-LINEAR-MAP-TYPE>\n\
\n\
</SEGMENTATION-PARAMETERS>\n'

		cmd = ABCCmd + ' ' + ABC_xml
		log = log + cmd + '\n'
		print cmd
		os.system(cmd)

		os.remove(DTI_up)
		DTI_up_t2 = DTI_up.replace('.nrrd','_T2AregB0Stripped.nrrd')
		DTI_up_b0idwi = DTI_up.replace('.nrrd','_ABCwB0iDWIStripped.nrrd')
		#Calculate the DTI for upsampled DWI
		if(os.path.exists(DTI_up_t2)==False):
		   cmd = 'dtiestim --dwi_image '+DWI_up_t2+' --tensor_output '+DTI_up_t2+' -m wls -M '+ BM_DTI_wT2
		   log = log + cmd + '\n'
		   print cmd
		   os.system(cmd)
		   cmd = 'dtiprocess '+DTI_up_t2+' -f '+DTI_up_t2.replace('TENSOR','FA') +' -m '+DTI_up_t2.replace('TENSOR','MD')+' --lambda1-output '+DTI_up_t2.replace('TENSOR','AD')+' --lambda2-output '+DTI_up_t2.replace('TENSOR','l2')+' --lambda3-output '+DTI_up_t2.replace('TENSOR','l3') + ' --scalar-float'
 		   print cmd
		   os.system(cmd)
 		   cmd = TImageMathCmd.substitute(infile=DTI_up_t2.replace('TENSOR','l2'),outfile= DTI_up_t2.replace('TENSOR','RD'))+' -add '+DTI_up_t2.replace('TENSOR','l3') +' -type float'
 		   print cmd
		   log = log + cmd + '\n'
 		   os.system(cmd)
 		   cmd = TImageMathCmd.substitute(infile=DTI_up_t2.replace('TENSOR','RD'),outfile= DTI_up_t2.replace('TENSOR','RD'))+' -constOper 3,2 -type float'
 		   print cmd
		   log = log + cmd + '\n'
 		   os.system(cmd)
 		   os.remove(DTI_up_t2.replace('TENSOR','L2'))
		   os.remove(DTI_up_t2.replace('TENSOR','L3'))
		if(os.path.exists(DTI_up_b0idwi)==False):
		   cmd = 'dtiestim --dwi_image '+DWI_up_b0idwi+' --tensor_output '+DTI_up_b0idwi+' -m wls -M '+ BM_DTI_wT2
		   log = log + cmd + '\n'
		   print cmd
		   os.system(cmd)
		   cmd = 'dtiprocess '+DTI_up_b0idwi+' -f '+DTI_up_b0idwi.replace('TENSOR','FA') +' -m '+DTI_up_b0idwi.replace('TENSOR','MD')+' --lambda1-output '+DTI_up_b0idwi.replace('TENSOR','AD')+' --lambda2-output '+DTI_up_b0idwi.replace('TENSOR','l2')+' --lambda3-output '+DTI_up_b0idwi.replace('TENSOR','l3') + ' --scalar-float'
 		   print cmd
		   os.system(cmd)
 		   cmd = TImageMathCmd.substitute(infile=DTI_up_b0idwi.replace('TENSOR','l2'),outfile= DTI_up_b0idwi.replace('TENSOR','RD'))+' -add '+DTI_up_b0idwi.replace('TENSOR','l3') +' -type float'
 		   print cmd
		   log = log + cmd + '\n'
 		   os.system(cmd)
 		   cmd = TImageMathCmd.substitute(infile=DTI_up_b0idwi.replace('TENSOR','RD'),outfile= DTI_up_b0idwi.replace('TENSOR','RD'))+' -constOper 3,2 -type float'
 		   print cmd
		   log = log + cmd + '\n'
 		   os.system(cmd)
 		   os.remove(DTI_up_b0idwi.replace('TENSOR','L2'))
		   os.remove(DTI_up_b0idwi.replace('TENSOR','L3'))
		
		f_log.write(log)
