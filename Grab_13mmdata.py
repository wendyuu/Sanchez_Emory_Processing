#! /usr/bin/env python
import os
import fnmatch
from string import Template
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile ')
TreorientCmd = Template('/tools/bin_linux64/imconvert3  $infile $outfile ')
ROOT_DIR = '/primate/SanchezEmory/BrainDevYerkes'
# prefix of the file names
prefixlist = open(os.path.join(ROOT_DIR,'processing/Subject_Prefix_List.txt'),'r');  
#the txt file that stores all the prefix names

for line in prefixlist:
	print 'Now Processing Subject ' + line;
	prefix = line[0:5];
	# unzip data in the /orig/ folder
	orig_loc =  os.path.join(ROOT_DIR,'13_T2_2009cohort/',prefix);
	dest_loc =  os.path.join(ROOT_DIR,prefix);

	for dir_tag in ['2_weeks','3_months']:
		dicom_loc = os.path.join(orig_loc,dir_tag);
		sMRI_loc = os.path.join(dest_loc,dir_tag.replace('_',''),'sMRI');		

		if os.path.exists(sMRI_loc):
		#DicomConvert
			print 'DicomConverting from ' + dicom_loc + ' to ' + sMRI_loc;
			# write the header file
			for file in os.listdir(dicom_loc):
				file = file.replace('\n','');
				# directory of the dicome file
				dicomname = os.path.join(dicom_loc,file);
			
				# convert T2
				if file.lower().find('T2'.lower()) >= 0:
					T2 = os.path.join(sMRI_loc,(prefix + '_' + dir_tag + '_13mm_T2.nhdr'))
					print 'DicomConverting ' + dicomname + ' to ' + T2;
					os.system('DicomConvert ' + dicomname + ' ' + T2 +' -v');
			
			os.system('rm -r '+dicom_loc);
			
			print 'Changing to T2 from NRRD to GIPL'
			T2_gipl = T2.replace('.nhdr','.gipl');
			if (os.path.exists(T2_gipl.replace('.gipl','.gipl.gz'))):
				print 'T2 GIPL already exists'
			else:
				convCmd = TconvCmd.substitute(infile=T2,outfile = T2_gipl);
				os.system(convCmd);
				print 'Done'
			print 'Changing the orientation of T2 from LAI to RAI'
			T2_RAI_gipl = T2.replace('T2.gipl','_T2_RAI.gipl');
			if (os.path.exists(T2_RAI_gipl)):
				print 'RAI already exists'
			else:
				reorientCmd = TreorientCmd.substitute(infile = T2_gipl,outfile = T2_RAI_gipl);
				os.system(reorientCmd + '-setorient LAI-RAI'); 
				print 'Done'


