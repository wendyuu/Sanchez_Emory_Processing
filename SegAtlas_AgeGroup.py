#! /usr/bin/env python

# Script to do skull stripping on T1 and T2 using Brainsmush and itkEMS
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
parser.add_option("-e","--EMS", action="store_true", dest="EMS", default=False)
parser.add_option("-b","--BM", action="store_true", dest="BM", default=False)
parser.add_option("-r","--RemoveAll", action="store_true", dest="rm", default=False)

(options, args) = parser.parse_args()

if options.filename:
   print 'Reading input from file '+options.filename
   prefixfile = os.path.join(ORIG_DIR,'processing',options.filename);
   prefixlist = open(prefixfile,'r');
elif len(args) > 0:
   print 'Reading input from the terminal'
   prefixlist = args;
   print args
else:
   print ('Input error: Either give a file name to read the prefix names of the subjects or type in from the terminal')
# VARIABLES SPECIFIC TO DATASET
ORIG_DATA_DIR = '/primate/CoeMonkeyFlu/'

# LOCATION VARIABLES for the atlas/template
atlasLoc = '/tools/atlas/BrainROIAtlas/rhesusMonkeyT1_RAI'
gridTemplate = atlasLoc + '/template.gipl'
atlasFile = atlasLoc + '/template.gipl'
atlasT2File = atlasLoc + 'templateT2.gipl'
atlasParcFile = atlasLoc + '/template_parc_vent.gipl'
atlasLabelHeaderFile = atlasLoc + '/labelList.txt'
atlasSubCortFile = atlasLoc + '/SubCortical.gipl'
atlasSubCortHeaderFile = atlasLoc + '/subcorticalList.txt'
atlasEMSFile = atlasLoc + '/template_hardseg.gipl'
brainmask = atlasLoc + '/Mask_WM_GM_CSF.gipl'
EMST1warp_orig = os.path.join(ORIG_DATA_DIR,'processing/T1name_to_template_EMSinfo.affine');  
EMST2warp_orig = os.path.join(ORIG_DATA_DIR,'processing/T1name_to_T2name_EMSinfo.affine');

# SYSTEM VARIABLES
# usually DO NOT EDIT THESE
from string import Template
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TrregCmd = Template('/tools/rview_linux64_2008/rreg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TintensityRescaleCmd = Template('/tools/bin_linux64/IntensityRescaler')
TimgConvCmd = Template('/usr/bin/convert')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
TwarpCmd = Template('/tools/bin_linux64/fWarp')
TImageMathCmd = Template('/tools/bin_linux64/ImageMath $infile -outfile $outfile')
TBMCmd =  Template('/home/yundi/local_tools/brainsmush_bin/BRAINSMush\
 --inputFirstVolume $Img1\
 --inputSecondVolume $Img2\
 --outputMask $BM\
 --lowerThresholdFactor $lower\
 --upperThresholdFactor $upper\
 --seed 256,124,256\
 --boundingBoxStart 64,31,64\
 --boundingBoxSize 128,62,128')

#itk EMS without registration
itkEMSNoregCmd = '/tools/bin_linux/itkEMS_noReg'
itkEMS18Cmd = '/tools/bin_linux64/itkEMS_1.8'

#recompute montage pictures?
recomputeMontage = 1

# the txt file that stores all the prefix names
parfile = os.path.join(ORIG_DATA_DIR ,'processing/Reg_par_NMI.txt')
# loop through the folders to calculate tensor
for prefix in prefixlist:
    #if 2weeks exists
	    curr_loc =  os.path.join(ORIG_DATA_DIR ,prefix);
	    print curr_loc
	    if os.path.exists(curr_loc):
	       # picture folder
	       		PicDir = os.path.join(curr_loc ,'pics');
	       		sMRIDir = os.path.join(curr_loc,'sMRI');
                        if(options.rm == True):
                           os.system('rm -rf '+sMRIDir)
                           print 'Clear sMRI folder and everything will be recalculated'
                        ANAT= os.path.join(ORIG_DATA_DIR,'orig_data',prefix,'anatomicals');
                        print 'Generating NRRD FILES'
			if (os.path.exists(sMRIDir)==False): os.system('mkdir ' + sMRIDir)
			T1 = os.path.join(sMRIDir, prefix  + '_T1.nrrd')
                        T2 = os.path.join(sMRIDir, prefix  + '_T2.nrrd')
                        PD = os.path.join(sMRIDir, prefix  + '_PD.nrrd')
                        
                        for file in fnmatch.filter(os.listdir(ANAT),'*bravo*'):
                           T1dicom = os.path.join(ANAT,file)
                           os.system('DicomConvert '+T1dicom+' '+T1);
                        
			for file in fnmatch.filter(os.listdir(ANAT),'*fse_xl*'):
                           #make temporay folders for T2 and PD dicoms
                           T2PDdicom = os.path.join(ANAT,file);
                           tempT2 = os.path.join(ANAT,'tempT2');
                           tempPD = os.path.join(ANAT,'tempPD');
                           os.mkdir(tempT2);
                           os.mkdir(tempPD);
                           for i in range(1,120,2):
                              sou=os.path.join(T2PDdicom,file+'.'+"%04d"%i);
                              os.system('cp '+sou+' '+tempPD);
                           os.system('DicomConvert '+tempPD+' '+PD);
                           os.system('rm -rf '+tempPD);
                              
                           for i in range(2,121,2):
                              sou=os.path.join(T2PDdicom,file+'.'+"%04d"%i);
                              os.system('cp '+sou+' '+tempT2);
                           os.system('DicomConvert '+tempT2+' '+T2);
                           os.system('rm -rf '+tempT2)
                           
	       		if (os.path.exists(PicDir)==False): os.system('mkdir ' + PicDir)
			
			# Procedure
			# A) Reorient as images are NOT in RAI but LSP
			# B) Use Brainsmush to strip out the gross structures like the eys and fat
			# C) Use EMS to do skull stripping
				#1) Register T2 to T1 image
				#2) Curve Smoothing
				#3) Init using rview manually
				#4) RunEMS
			# 8) Mask brain of T1
			# 9) Warping etc
			#

			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------		
                        # ---------------------------------------------------------------------
			# 1) Reorient as images are NOT in RAI but RSP
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
                        
			print 'Changing to T1 from NRRD to GIPL'
			
			T1_gipl = T1.replace('.nrrd','.gipl');
			convCmd = TconvCmd.substitute(infile=T1,outfile = T1_gipl);
			os.system(convCmd);
                        
			T1_RAI_gipl = os.path.join(sMRIDir,prefix  + '_T1_RAI.gipl')
			reorientCmd = TreorientCmd.substitute(infile = T1_gipl,outfile = T1_RAI_gipl);
			os.system(reorientCmd + '-setorient LSP-RAI');
                        
                        
			#---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# 2) Register T2 to T1 image
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			RregRedo = 0;
			print '\
##########################################################\n\
###############Registering T2 to the T1#################\n\
##########################################################\n'
			print 'Changing to T2 from NRRD to GIPL'
			
			T2_gipl = T2.replace('.nrrd','.gipl');
			convCmd = TconvCmd.substitute(infile=T2,outfile = T2_gipl);
                        os.system(convCmd);
			
			print 'Changing the orientation of T2 from LSP to RAI'
			T2_RAI_gipl = T2_gipl.replace('.gipl','_RAI.gipl');
			reorientCmd = TreorientCmd.substitute(infile = T2_gipl,outfile = T2_RAI_gipl);
			os.system(reorientCmd + '-setorient LSP-RAI'); 
			 
			T2RregT1  = T2_RAI_gipl.replace('.gipl','_RregT1.gipl')
			dofoutRreg = T2RregT1.replace('.gipl','.dof');
			if (os.path.exists(dofoutRreg) == False or RregRedo == 1):
                            rregCmd = TrregCmd.substitute(tar = T1_RAI_gipl, sou = T2_RAI_gipl) + ' -dofout ' + dofoutRreg + ' -parin ' +  parfile + ' -Tp 5';
                            os.system(rregCmd)
                            transformCmd = TtransformCmd.substitute(sou = T2_RAI_gipl, out = T2RregT1, dofin = dofoutRreg) + ' -target ' + T1_RAI_gipl + ' -cspline';
                            os.system(transformCmd)          

			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# B) Run Brainsmush to do a gross structure stripping
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# Fundamental parameters
			SSDir = os.path.join(sMRIDir,'BM_EMS_SkullStripped')
                        if(options.rm == True):
                           os.system('rm -rf '+SSDir);
			T1_BM = T1_RAI_gipl.replace(sMRIDir,SSDir).replace('_RAI','_BMStripped')
			T2_BM = T2RregT1.replace(sMRIDir,SSDir).replace('_RAI','_BMStripped');
			if (os.path.exists(SSDir)==False):  os.system('mkdir '+SSDir)
			if (options.BM == True):
			   lower = 135
			   upper = 60;
			   T2_nii = T2RregT1.replace('gipl','nii.gz')
                	   T1_nii = T1_RAI_gipl.replace('gipl','nii.gz')
                	   os.system(TconvCmd.substitute(infile=T1_RAI_gipl,outfile=T1_nii));
			   os.system(TconvCmd.substitute(infile=T2RregT1,outfile=T2_nii));
			   # Run Brainsmush	    
			   BrainMask = T1_nii.replace('T1_RAI','BM_brainMask').replace(sMRIDir,SSDir);
        	      	   
        	      	   if (os.path.exists(T1_BM) == False or options.BM == True):			   
	        	      xml = T1_nii.replace('T1_RAI.nii.gz','BM.xml').replace(sMRIDir,SSDir)
        	              BMCmd = TBMCmd.substitute(Img1=T1_nii,Img2=T2_nii,BM=BrainMask,upper=upper/100.0, lower=lower/100.0);
                	      fout = open(xml,'w');
			      fout.write(BMCmd);
			      fout.close();
                              print BMCmd
                	      os.system(BMCmd)
	                      os.system('SegPostProcess ' + BrainMask + ' -o ' + BrainMask + ' -v');
			   
			   # Do skull stripping
		    	   print 'Initial Stripping T1 Using BrainsMush'
			   ImageMathCmd = TImageMathCmd.substitute(infile = T1_RAI_gipl,outfile = T1_BM) + ' -mask ' + BrainMask
    			   os.system(ImageMathCmd)
			   print 'Initial Stripping T2 Using BrainsMush'
			   ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2_BM) + ' -mask ' + BrainMask
    			   os.system(ImageMathCmd)  

			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# B) Run EMS using the old atlas for skull stripping
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			# ---------------------------------------------------------------------
			
			# Fundamental parameters
			regtar = 'T1_RAI_gipl';
                        EMSreg = 0;
			SUFFIX = 'EMS_v18'
                        T1_EMS = T1_BM.replace('BMStripped','EMSStripped')
			T2_EMS = T2_BM.replace('BMStripped','EMSStripped')

			brainmask = os.path.join(SSDir,'EMS_brainMask.gipl')
			if (options.EMS == True):
			   print 'Run itkEMS for skull stripping'
			   EMSfile  = os.path.join(SSDir,(SUFFIX+'param.xml')); 
			   Aregfile  = os.path.join(SSDir,('PreAreg_'+SUFFIX+'.xml')); 
			   if (EMSreg == 0):
			      # trick to disable warping in EMS
     			      # cp the transformation file with identity trans to the tmp folder
			       EMST1warp_tar = EMST1warp_orig.replace((ORIG_DATA_DIR+'processing'),SSDir).replace('T1name',prefix+  '_T1_RAI').replace('EMSinfo',SUFFIX);
			       EMST2warp_tar = EMST2warp_orig.replace((ORIG_DATA_DIR+'processing'),SSDir).replace('T1name',prefix+  '_T1_RAI').replace('T2name',prefix+  '_T2_RAI_RregT1').replace('EMSinfo',SUFFIX);
			       os.system('cp '+ EMST1warp_orig + ' ' + EMST1warp_tar);
			       os.system('cp '+ EMST2warp_orig + ' ' + EMST2warp_tar);

			   # 1 - 1. affinely align atlas to the subject and make subject specific atlas
			   newTemplate = atlasFile.replace(atlasLoc,SSDir);
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
			   for parc in ['template','white','gray','csf','rest']:
			       if (os.path.exists(os.path.join(SSDir,parc+'.gipl'))==False):
				  print 'Transforming'+parc+'.gipl'
				  transformCmd = TtransformCmd.substitute(sou = atlasFile.replace('template',parc), out = newTemplate.replace('template',parc), dofin = dof) + ' -target ' + T1_RAI_gipl + ' -cspline';
				  os.system(transformCmd)
				  fareg.write(transformCmd+'\n'+'\n');
                           fareg.close();
			
			
			   # 2. edit pixdims for all images in SSDir
			   # 2-1 Get the original pixel information
		           origPixdim = os.popen('ImageStat '+T1_RAI_gipl+' -info | grep Pixdims').read()
			   origdim = os.popen('ImageStat '+T1_RAI_gipl+' -info | grep Dims').read()
			   origPixdims = str(origPixdim).split(' ');
			   origdims = str(origdim).split(' ');

			   # 2-2 Change pixdim to 1.0*1.0*1.0				
			   giplpattern = '*.gipl*'
			   for image in fnmatch.filter(os.listdir(SSDir),giplpattern):
				ImageMathCmd = TImageMathCmd.substitute(infile = os.path.join(SSDir,image), outfile = os.path.join(SSDir,image)) + ' -editPixdims 1.0,1.0,1.0'
	    			os.system(ImageMathCmd)
			   ImageMathCmd = TImageMathCmd.substitute(infile = T1_RAI_gipl, outfile = T1_RAI_gipl) + ' -editPixdims 1.0,1.0,1.0'
	    		   os.system(ImageMathCmd)
			   ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2RregT1) + ' -editPixdims 1.0,1.0,1.0'
	    		   os.system(ImageMathCmd)
			   # change the origins in the registration accordingly
			   for dim in [1,2,3]:
				for sub in ['sou','tar']:
					tag = (sub+str(dim)).capitalize();
					cons = 1.0*float(origdims[dim]);
					#for filetag in ['T1','T2']:
						#warpname = eval('EMS'+filetag+'warp_tar');
						#os.system('text_subst.pl ' + tag + ' ' +str(cons) +' ' +warpname)	
			   # 3. perform itkEMS-based segmentation
			   # 3-1 create EMS file
			   if SUFFIX == 'EMS_v18':
				EMS_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+SSDir+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+SSDir+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>GIPL</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+T1_RAI_gipl+'</FILE>\n\
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
			   if SUFFIX == 'EMS_noReg':
				EMS_info = '<?xml version="1.0"?>\n\
<!DOCTYPE SEGMENTATION-PARAMETERS>\n\
<SEGMENTATION-PARAMETERS>\n\
<SUFFIX>'+SUFFIX+'</SUFFIX>\n\
<ATLAS-DIRECTORY>'+SSDir+'</ATLAS-DIRECTORY>\n\
<ATLAS-ORIENTATION>RAI</ATLAS-ORIENTATION>\n\
<OUTPUT-DIRECTORY>'+SSDir+'</OUTPUT-DIRECTORY>\n\
<OUTPUT-FORMAT>GIPL</OUTPUT-FORMAT>\n\
<IMAGE>\n\
  <FILE>'+T1_RAI_gipl+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<IMAGE>\n\
  <FILE>'+T2RregT1+'</FILE>\n\
  <ORIENTATION>RAI</ORIENTATION>\n\
</IMAGE>\n\
<FILTER-ITERATIONS>5</FILTER-ITERATIONS>\n\
<FILTER-TIME-STEP>0.01</FILTER-TIME-STEP>\n\
<MAX-BIAS-DEGREE>1</MAX-BIAS-DEGREE>\n\
<PRIOR-1>0.5</PRIOR-1>\n\
<PRIOR-2>0.5</PRIOR-2>\n\
<PRIOR-3>0.5</PRIOR-3>\n\
<PRIOR-4>0.1</PRIOR-4>\n\
</SEGMENTATION-PARAMETERS>\n'
			   fout = open(EMSfile,'w');
			   fout.write(EMS_info);
			   fout.close();
	
			   if (os.path.exists(os.path.join(SSDir,'*_EMS*.gipl*')) == False or options.EMS == True): 
				# 3-2 run EMS
				print itkEMS18Cmd + ' ' + EMSfile
				os.system(itkEMS18Cmd + ' ' + EMSfile)
			
				# 3-4 reduce intensity space from 0...32k to 0..1024
				for image in fnmatch.filter(os.listdir(SSDir),'*_corrected_EMS.gipl*'):
	    				ImageMathCmd = TImageMathCmd.substitute(infile = image, outfile = image) + '  -constOper 3,32'
					os.system(ImageMathCmd)
				for image in fnmatch.filter(os.listdir(SSDir),'*_posterior*_EMS.gipl*'):
	    				ImageMathCmd = TImageMathCmd.substitute(infile = image, outfile = image) + '  -constOper 3,32'
					os.system(ImageMathCmd)

				# 3-5 edit back the pixel size
				for image in fnmatch.filter(os.listdir(SSDir),giplpattern):
                                   ImageMathCmd = TImageMathCmd.substitute(infile = SSDir+'/'+image, outfile = SSDir+'/'+image) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
                                   os.system(ImageMathCmd);                                        
				ImageMathCmd = TImageMathCmd.substitute(infile = T1_RAI_gipl, outfile = T1_RAI_gipl) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
	    		        os.system(ImageMathCmd)
			   	ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2RregT1) + ' -editPixdims '+origPixdims[1]+','+origPixdims[2]+','+origPixdims[3].replace('\n','')
	    		   	os.system(ImageMathCmd)
		
			   # 8. mask the brain
			   # ---------------------------------------------------------------------
			   # ---------------------------------------------------------------------
			   # ---------------------------------------------------------------------

			   print 'Doing Skull Stripping'


			   for img in fnmatch.filter(os.listdir(SSDir),'*labels_'+SUFFIX+'.gipl'):
				brainmaskIn = os.path.join(SSDir,img);

			   print 'Creating Brain Mask'
			   os.system('SegPostProcess ' + brainmaskIn + ' -o ' + brainmask + ' -v');

			if (os.path.exists(T1_EMS)==False):
  			   print 'Stripping T1'
    			   ImageMathCmd = TImageMathCmd.substitute(infile = T1_RAI_gipl, outfile = T1_EMS) + ' -mask ' + brainmask
			   print ImageMathCmd
    			   os.system(ImageMathCmd)
			   
			if (os.path.exists(T2_EMS)==False):
			   print 'Stripping T2'
    			   ImageMathCmd = TImageMathCmd.substitute(infile = T2RregT1, outfile = T2_EMS) + ' -mask ' + brainmask
			   print ImageMathCmd
    			   os.system(ImageMathCmd)
			


