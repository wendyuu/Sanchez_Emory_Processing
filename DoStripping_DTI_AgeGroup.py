#! /usr/bin/env python

# Script to do skull stripping on DTI images
# 1) Use itkEMS of iDWI/b0 as dual channels
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
	prefixfile = os.path.join(ORIG_DATA_DIR,'processing',options.filename);
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
TclampCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu 3op clamp $min $infile $max -o $infile')
TupsampleCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu resample -i $sou -o $out -s $dim -k hann:15')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TintensityRescaleCmd = Template('/tools/bin_linux64/IntensityRescaler')
TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TwarpCmd = Template('/tools/bin_linux64/fWarp')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
ThistmatchCmd = Template('/tools/bin_linux64/ImageMath $sou -matchHistogram $tar -outfile $out')
TunusaveCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -i $infile -o $outfile')
TChangeSpaceDir = Template('/primate/SanchezEmory/BrainDevYerkes/processing/ChangeSpaceDir.py $infile $outfile')

#itk EMS without registration
itkEMSNoregCmd = '/tools/bin_linux/itkEMS_noReg'
itkEMS18Cmd = '/tools/bin_linux64/itkEMS_1.8'
unuhead = '/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu head '
parfile = os.path.join(ORIG_DATA_DIR,'processing','Reg_par_CC.txt')
parfile_bsp = os.path.join(ORIG_DATA_DIR,'processing','Reg_par_CC_Bspline.txt')
redo = 1;
tag_template_exist = 0;

# loop through the folders to calculate tensor
for line in prefixlist:
	    prefix = line[0:5];
	    #if 2weeks exists
	    curr_loc =  os.path.join(ORIG_DATA_DIR,prefix,dir_tag);
	    DTIDir = os.path.join(curr_loc,'DTI');
	    if os.path.exists(DTIDir):
	       	###############VARIABLES#################
	       	PicDir = os.path.join(curr_loc ,'pics');
		DTIDir = os.path.join(curr_loc,'DTI');		
		sMRIDir = os.path.join(curr_loc,'sMRI');
		scale = 2;
		#pixel dim to upsample the volumes to
		# save nhdr to nrrd in gzip
		if(fnmatch.filter(os.listdir(DTIDir),prefix+'_'+dir_tag+'_30dir_10DWI_*addB0.nhdr')):
			nhdr = os.path.join(DTIDir,fnmatch.filter(os.listdir(DTIDir),prefix+'_'+dir_tag+'_30dir_10DWI_*addB0.nhdr')[0]);
			DWI = nhdr.replace('.nhdr','.nrrd')
			print 'Saving nhdr to nrrd in gzip'
			cmd = TunusaveCmd.substitute(infile=nhdr,outfile=DWI)+' -e gzip';		
			os.system(cmd)
			os.remove(nhdr)
		else:
			DWI = os.path.join(DTIDir,fnmatch.filter(os.listdir(DTIDir),prefix+'_'+dir_tag+'_30dir_10DWI_*addB0.nrrd')[0]);
		raw = DWI.replace('.nrrd','.raw')
		rawgz = DWI.replace('.nrrd','.raw.gz')

		if(os.path.exists(raw)):  os.remove(raw)
		if(os.path.exists(rawgz)):  os.remove(rawgz)
		
		nhdrContent = os.popen(unuhead+DWI).read()
		text_str_size = nhdrContent.split('\n')[7];
		print text_str_size
		dim1 = int(text_str_size.split(' ')[1])
		dim2 = int(text_str_size.split(' ')[2])
		dim3 = int(text_str_size.split(' ')[3])	
		
		sMRI_SSDir = os.path.join(sMRIDir,'Tissue_Seg_ABC');
		T1 = os.path.join(sMRIDir,prefix + '_' + dir_tag +  '_T1_050505mm_RAI.gipl.gz');
		T2 = os.path.join(sMRIDir,prefix+'_'+dir_tag+'_T2_050510mm_RAI_N3corrected_RregT1.nhdr');
		sMRIbrainmask = os.path.join(sMRI_SSDir,'ABC_brainMask.gipl.gz')
		print sMRIbrainmask
		 
		print 'Generate B0 using naive thresholding'

		# Do simple thresholding using iDWI
		BM_DTI = os.path.join(DTIDir,'brainMask_T2AregB0T105_upsampled.gipl.gz');
		B0 = DWI.replace(prefix+'_','B0'+'_'+prefix+'_');
		iDWI = DWI.replace(prefix+'_','iDWI'+'_'+prefix+'_');
		DTI = DWI.replace(prefix+'_','TENSOR'+'_'+prefix+'_');
		
		if(os.path.exists(BM_DTI)==False):
		   if(os.path.exists(B0)==False):
		      dtiestim_cmd = 'dtiestim '+DWI+' '+DTI+' -m wls -t 20 --B0 '+B0 +' --idwi '+iDWI
		      print dtiestim_cmd
		      os.system(dtiestim_cmd)
		    
		
		   #########################################
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # 1) Reorient as images are NOT in RAI but RSP
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   B0_gipl = B0.replace('.nrrd','.gipl');  
		   if(os.path.exists(B0_gipl)==False):
			   print 'Change nrrd to gipl format'		
			   convCmd = TconvCmd.substitute(infile=B0,outfile = B0_gipl);
			   os.system(convCmd);
		   B0_RAI_gipl = B0_gipl.replace('.gipl','_RAI.gipl.gz')
		   print B0_RAI_gipl
		   if (os.path.exists(B0_RAI_gipl)==False):
		        print 'Changing the orientation of B0 from LAI to RAI'
			#imconvert3 doesn't deal with .gz file
			reorientCmd = TreorientCmd.substitute(infile = B0_gipl,outfile = B0_RAI_gipl.replace('.gipl.gz','.gipl'));
			print reorientCmd  #for debugging
			os.system(reorientCmd + '-setorient LAI-RAI');
			os.system('rm '+B0_gipl)
			os.system('gzip '+B0_RAI_gipl.replace('.gipl.gz','.gipl'))
			
		   # generating grid template for brain mask
		   print 'Generating grid template '+grid_template+' for the brainmask'
		   if(os.path.exists(grid_template)==False):
			upsampleCmd = TupsampleCmd.substitute(sou = B0, out = grid_template.replace('gipl.gz','nrrd'), dim=str(dim1*scale)+' '+str(dim2*scale)+' '+str(dim3*scale));
			print upsampleCmd
			os.system(upsampleCmd)
			convCmd = TconvCmd.substitute(infile=grid_template.replace('gipl.gz','nrrd'),outfile=grid_template)
			os.system(convCmd)
			os.system('rm '+grid_template.replace('gipl.gz','nrrd'));
			tag_template_exist=1;
		   
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
		   # B) Affine registration of T2 to B0 and transform the T1brainmask accordingly
		   # ---------------------------------------------------------------------
		   # ---------------------------------------------------------------------
	           # --------------------------------------------------------------------

		   print 'Generating Brain Mask by Transforming the T2 Brainmask'
	           dofoutAreg = B0_RAI_gipl.replace('.gipl.gz','T2Areg.dof');
		   # Registering T2 to B0 using bspline affine 
	           if(os.path.exists(dofoutAreg)==False):
			   aregCmd = TaregCmd.substitute(tar = B0_RAI_gipl, sou = T2) + ' -dofout ' + dofoutAreg + ' -parin ' +  parfile + ' -Tp 5';
			   print aregCmd
			   os.system(aregCmd)
			   aregCmd = TaregCmd.substitute(tar = B0_RAI_gipl, sou = T2) + ' -dofin ' + dofoutAreg + ' -dofout ' + dofoutAreg  + ' -parin ' +  parfile_bsp + ' -Tp 5';
			   os.system(aregCmd)
		   # Transform the T2 brain mask accordingly
		   print 'Transform the T2 brain mask accordingly'
		   if(os.path.exists(BM_DTI)==False):
			   transformCmd = TtransformCmd.substitute(sou = sMRIbrainmask, out = BM_DTI, dofin = dofoutAreg) + ' -target ' + grid_template + ' -cspline';
			   os.system(transformCmd)
			   print 'Change the BM orientation back to the tensor space'
			   os.system('gunzip '+BM_DTI)
			   reorientCmd = TreorientCmd.substitute(infile = BM_DTI.replace('.gipl.gz','.gipl'),outfile = BM_DTI.replace('.gipl.gz','.gipl'))
			   print reorientCmd+' -setorient RAI-LAI'
			   os.system(reorientCmd + ' -setorient RAI-LAI')
			   os.system('gzip '+BM_DTI.replace('.gipl.gz','.gipl'))
		   # remove the inital B0
#		   if(os.path.exists(B0)): os.remove(B0)
#		   if(os.path.exists(B0_RAI_gipl)):os.remove(B0_RAI_gipl)
#		   if(os.path.exists(iDWI)):os.remove(iDWI)
                   #else:
		   # change the space dir, origin and measurement frame of the BM
		   ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=BM_DTI,outfile=BM_DTI)
		   print ChangeSpaceDirCmd
		   os.system(ChangeSpaceDirCmd)
							      
	# 	DWI_up = DWI.replace('.nrrd','_upsampled.nrrd').replace('.nhdr','_upsampled.nhdr')
# 		print 'Calculating Tensor with the Brainmask'
# 		B0 = DWI_up.replace(prefix+'_','B0'+'_'+prefix+'_');
# 		iDWI = DWI_up.replace(prefix+'_','iDWI'+'_'+prefix+'_');
# 		DTI = B0.replace('B0_'+prefix,'TENSOR_'+prefix)
# 		FA = B0.replace('B0_'+prefix,'FA_'+prefix)
# 		MD = FA.replace('FA_','MD_')
# 		AD = FA.replace('FA_','AD_')
# 		L2 = FA.replace('FA_','L2_')
# 		L3 = FA.replace('FA_','L3_')
# 		RD = FA.replace('FA_','RD_')
# 		#upsample the DWIs using windowed sinc
# 		print 'upsample the DWIs using windowed sinc to '+str(dim1*scale)+'*'+str(dim2*scale)+'*'+str(dim3*scale)
# 		if(os.path.exists(DWI_up)==False):
# 		   upsampleCmd = TupsampleCmd.substitute(sou = DWI, out = DWI_up, dim=str(dim1*scale)+' '+str(dim2*scale)+' '+str(dim3*scale)+' =');
# 		   print upsampleCmd
# 		   os.system(upsampleCmd)
# 		   # Get rid of negative values
# 		   cmd = TclampCmd.substitute(infile=DWI_up,min='0',max=str(10000000))
# 		   print cmd
# 		   os.system(cmd)
# 		   # gzip the file
# 		   cmd = TunusaveCmd.substitute(infile=DWI_up,outfile=DWI_up)+' -e gzip';
# 		   print cmd
# 		   os.system(cmd)
# 		else:
# 			pass

# 		ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=DWI_up,outfile=DWI_up)+' --dwi --noCenter'
# 		print ChangeSpaceDirCmd
# 		os.system(ChangeSpaceDirCmd)
									    
		    
# 		#Calculate the DTI for upsampled DWI
# 		if(os.path.exists(DTI)==False or redo == 1):
# 		   cmd = 'dtiestim '+DWI_up+' '+DTI+' -m wls -M '+ BM_DTI
# 		   #  --B0 '+B0 +' --idwi '+ iDWI+'
# 		   if(os.path.exists(DTI)==False or redo == 1):
# 		      print cmd
# 		      os.system(cmd)
# 		     # ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=DWI,outfile=DWI)+' --dwi'
# 		     # print ChangeSpaceDirCmd
# 		     # os.system(ChangeSpaceDirCmd)
# 		   cmd = 'dtiprocess '+DTI+' -f '+FA +' -m '+MD+' --lambda1-output '+AD+' --lambda2-output '+L2+' --lambda3-output '+L3 + ' --scalar-float'
#  		   print cmd
# 		   os.system(cmd);
#  		   cmd = TImageMathCmd.substitute(infile=L2,outfile= RD)+' -add '+L3 +' -type float';
#  		   print cmd
#  		   os.system(cmd);
#  		   cmd = TImageMathCmd.substitute(infile=RD,outfile= RD)+' -constOper 3,2 -type float';
#  		   print cmd
#  		   os.system(cmd);
#  		   os.remove(L2)
# 		   os.remove(L3)
