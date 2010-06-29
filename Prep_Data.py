#! /usr/bin/env python

# Script to unzip data including T1, 6mmT1 and T2 and converting them to nrrd
# converting DTI as well and form a large DWI based on all the dwis

import os
import fnmatch
import sys
from optparse import OptionParser

ORIG_DIR = '/primate/SanchezEmory/BrainDevYerkes/'

print 'Usage \n\
[subject_list]\n\
-f [subject_file]\n\
-d (dtionly)\n\
-s (smrionly)\n\
-m (nodicom)\n\
-a (age, which will be the surfix as well)\n'
# prefix of the file names
# either read it from a file or as input
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)

parser.add_option("-f", "--file", dest="filename",
                  help="read data from FILE", metavar="FILE")
parser.add_option("-a", "--age", dest="dir_tag",
                  help="age and the dir tag")
parser.add_option("-d","--dti", action="store_true", dest="dtionly", default=False)
parser.add_option("-s","--smri", action="store_true", dest="smrionly", default=False)
parser.add_option("-m","--nodicom", action="store_true", dest="nodicom", default=False)

#whether or not to do dicom convert

(options, args) = parser.parse_args()
print args
if options.filename:
   print 'Reading input from file '+options.filename
   prefixfile = os.path.join(ORIG_DIR,'processing',options.filename);
   prefixlist = open(prefixfile,'r');
elif len(args) > 0:
   print 'Reading input from the terminal'
   prefixlist = args[:];
else:
   print ('Input error: Either give a file name to read the prefix names of the subjects or type in from the terminal')

from string import Template
TCombineNrrdCmd = Template('/tools/bin_linux64/CombineDWI.py $outfile $dwilist -b $b0list')
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64/bin/unu save -f nrrd -e gzip -i $infile -o $outfile')
TunujoinCmd = Template('/tools/Slicer3/Slicer3-3.6-2010-06-10-linux-x86_64/bin/unu join -a 3 -i $infile |/tools/Slicer3/Slicer3-3.4.2-2010-01-06-linux-x86_64/bin/unu save -f nrrd -e gzip -o $outfile')


b0pattern = '*b0*'
diffpattern = '*diff*'

for line in prefixlist:
   print 'Now Processing Subject ' + line
   prefix = line[0:5]
   suffix = options.dir_tag  # the second data transfer on Dec-21st
   
   curr_loc =  os.path.join(ORIG_DIR,prefix)
   if(os.path.exists(curr_loc)==False): os.system('mkdir ' + curr_loc)
   curr_loc =  os.path.join(curr_loc,suffix)
   if(os.path.exists(curr_loc)==False): os.system('mkdir ' + curr_loc)
  
   # mkdir the sMRI and DTI folder
   sMRI_loc =  os.path.join(curr_loc,'sMRI')
   if(os.path.exists(sMRI_loc)==False): os.system('mkdir ' + sMRI_loc)
   print sMRI_loc
   DTI_loc =  os.path.join(curr_loc,'DTI')
   if(os.path.exists(DTI_loc)==False): os.system('mkdir ' + DTI_loc)
   print sMRI_loc
   
   B0_namecounter = 0
   DWI_namecounter = 0
   T16name = os.path.join(sMRI_loc,prefix  + '_'+suffix+'_T1_060606mm.nrrd')
   T15name = os.path.join(sMRI_loc,prefix  + '_'+suffix+'_T1_050505mm.nrrd')
   T2name = os.path.join(sMRI_loc,prefix  + '_'+suffix+'_T2_050510mm.nrrd')
   print prefix
   print suffix
   if(options.nodicom == False):
      # for all the zipnames that contain prefix and suffix
      # format of the zip file would be **R??13_[age]*
      dicom_loc = os.path.join(ORIG_DIR,'orig')
      for file in fnmatch.filter(os.listdir(dicom_loc),'*'+prefix+'_'+suffix+'*zip'):
         zipname = os.path.join(dicom_loc,file.replace('.zip',''))
         # unzip not done
         print 'Now Processing Subject ' + prefix + suffix
         print zipname
         if (os.path.exists(zipname) == False):
            cmd = 'unzip ' + zipname + '.zip -d ' + dicom_loc
            print cmd
            os.system(cmd)
         
         for folder in os.listdir(zipname):   
            # convert T1_06mm
            print folder
            if folder.lower().find('666'.lower())>= 0 and options.dtionly==False and os.path.exists(T16name)==False:
               print 'DicomConverting ' + zipname + ' to ' + T16name
               os.system('DicomConvert ' + os.path.join(zipname,folder) + ' ' + T16name +' -v')
               cmd = TunugzipCmd.substitute(infile=T16name,outfile=T16name)
               print cmd
               os.system(cmd)
	       os.system('rm -rf ' + os.path.join(zipname,folder))
               # convert T1_05mm
            elif folder.lower().find('t2'.lower())>= 0 and options.dtionly==False and os.path.exists(T2name)==False:
               print 'DicomConverting ' + zipname + ' to ' + T2name
               os.system('DicomConvert ' + os.path.join(zipname,folder) + ' ' + T2name +' -v')
               cmd = TunugzipCmd.substitute(infile=T2name,outfile=T2name)
               print cmd
               os.system(cmd)
               os.system('rm -rf ' + os.path.join(zipname,folder))
            elif folder.lower().find('t1'.lower())>= 0 and options.dtionly==False and os.path.exists(T15name)==False:
               print 'DicomConverting ' + zipname + ' to ' + T15name
               os.system('DicomConvert ' + os.path.join(zipname,folder) + ' ' + T15name +' -v')
               os.system('rm -rf ' + os.path.join(zipname,folder))
               cmd = TunugzipCmd.substitute(infile=T15name,outfile=T15name)
               print cmd
               os.system(cmd)           
            elif (fnmatch.fnmatch(folder.lower(),b0pattern)==True):
               B0name = os.path.join(DTI_loc,prefix+'_'+suffix+'_diff_30dir_B0_'+"%02d"%B0_namecounter+'.nhdr')
               dicomname = os.path.join(zipname,folder)
               if(os.path.exists(B0name) == False or os.path.exists(B0name.replace('.nhdr','.raw.gz')) == False):
                  cmd = 'DicomToNrrdConverter --inputDicomDirectory ' + dicomname + ' --outputVolume ' + B0name
                  os.system(cmd)
                  print cmd
                  cmd = TunugzipCmd.substitute(infile=B0name,outfile=B0name)
                  print cmd
                  os.system(cmd)
                  if os.path.exists(B0name.replace('.nhdr','.raw')):
                     os.remove(B0name.replace('.nhdr','.raw'))
               B0_namecounter = B0_namecounter+1
                  
            elif fnmatch.fnmatch(folder.lower(),diffpattern) == True:
               DWIname = os.path.join(DTI_loc,prefix+'_'+suffix+'_diff_30dir_' + "%02d"%DWI_namecounter + '.nhdr')
               dicomname = os.path.join(zipname,folder)
               if(os.path.exists(DWIname)==False or os.path.exists(DWIname.replace('nhdr','raw.gz'))==False):
                  cmd = 'DicomToNrrdConverter --inputDicomDirectory ' + dicomname + ' --outputVolume ' + DWIname
                  print cmd
                  os.system(cmd)              
                  cmd = TunugzipCmd.substitute(infile=DWIname,outfile=DWIname)
                  print cmd
                  os.system(cmd)
                  if os.path.exists((DWIname.replace('.nhdr','.raw'))):
                     os.remove(DWIname.replace('.nhdr','.raw'))
               DWI_namecounter = DWI_namecounter + 1
   
   B0_counter = 0
   DWI_counter = 0
   
   dwi_list = ''
   b0_list = ''
   # IMPORTANT NOTE:  Gradient matching between the data file and the header file
   if(options.smrionly == False):
      #Get the sequence in ordering the raw files
      for file in os.listdir(DTI_loc):
         if(fnmatch.fnmatch(file,'*_'+suffix+'_diff_30dir_B0_*nhdr')==True):
            B0_counter += 1
         elif(fnmatch.fnmatch(file,'*'+'_'+suffix+'_diff_30dir_*nhdr')==True):
            DWI_counter += 1
      printout = 'there are ' + str(B0_counter) + ' additional B0 images and ' + str(DWI_counter) + ' DWI sets\n'		
      print printout

#       nhdrContent = ''
#       tag_line = 0
#       gradnum = 0
      for i in range(0,DWI_counter):
         DWIname = os.path.join(DTI_loc,prefix+'_'+suffix+'_diff_30dir_' + "%02d"%i + '.nhdr')
         if(i == 0):
            dwi_list = DWIname
         else:
            dwi_list = dwi_list +  ',' + DWIname
#          lnum = 1 #line number# for the large combined DWI data
#          fin = open(DWIname,'r')
#          # read the gradient directions
#          # write the gradient directions
#          for line in fin:
#             lnum += 1
#             if lnum >= 22:
#                addline = 'DWMRI_gradient_'+"%04d"%gradnum + ':=' + line[21:]
#                nhdrContent = nhdrContent + addline
#                gradnum +=1
#                tag_line = 1
#             ##############*******************###################**************
#             ###########number is 5 because it's raw.gz or would be 2 for raw
#             #####################************************#####################
#             elif(tag_line==0 and lnum>5 and lnum<22):
#                nhdrContent = nhdrContent + line
#          fin.close()

      for i in range(0,B0_counter):
         B0name = os.path.join(DTI_loc,prefix+'_'+suffix+'_diff_30dir_B0_' + "%02d"%i + '.nhdr')
         if(i == 0):
            b0_list = B0name
         else:
            b0_list = b0_list +  ',' + B0name
#          addline = 'DWMRI_gradient_'+"%04d"%gradnum + ':=0   0   0\n'
#          nhdrContent = nhdrContent + addline
#          gradnum +=1
        
      # the output .nhdr file
      foutnhdr = os.path.join(DTI_loc,prefix+'_'+suffix+'_30dir_'+str(DWI_counter)+'DWI')+ '_'+str(B0_counter)+'addB0.nhdr'
      foutraw = foutnhdr.replace('nhdr','raw.gz')

      #combine all the nurrd
      if (os.path.exists(foutraw)==False or os.path.exists(foutnhdr)==False):
         cmd = TCombineNrrdCmd.substitute(outfile=foutnhdr,b0list=b0_list,dwilist=dwi_list)
         print cmd
         os.system(cmd)
         #generate raw file
         
      # if (os.path.exists(foutraw)==False):
#          #generate raw file
#          GenrawCmd = TunujoinCmd.substitute(infile=raw_file_list,outfile=foutnhdr)
#          print GenrawCmd
#          os.system(GenrawCmd)
      
#       # Modify the header file
#       nhdrContent = 'NRRD0005\ncontent: exists(' + foutraw + ',0)\n' + nhdrContent
#       nhdrContent.replace('content: exists(*,0)','content: exists(' + foutraw + ',0)')
#       nhdrContent.replace('data file: *\n','data file: ' + foutraw + '\n')
#       #############***************################*************###############
#       # [7] is for raw.gz [5] should be used for raw
#       text_str_size = nhdrContent.split('\n')[5]
#       ##################******************####################***************
#       text = text_str_size.split(' ')[0]
#       dim1 = text_str_size.split(' ')[1]
#       dim2 = text_str_size.split(' ')[2]
#       dim3 = text_str_size.split(' ')[3]
      
#       nhdrContent = nhdrContent.replace(str(text_str_size),(text+' '+dim1+' '+dim2+' '+dim3+' '+str(gradnum)))
      
#       text_data_file = nhdrContent.split('\n')[15]
#       txt_data = text_data_file.split(' ')[0]
#       txt_file = text_data_file.split(' ')[1]
#       nhdrContent = nhdrContent.replace(text_data_file,(txt_data+' '+txt_file+' '+ foutraw))

#       encoding_raw = nhdrContent.split('\n')[11]
#       nhdrContent = nhdrContent.replace(encoding_raw,'encoding: gzip')
   
#       fout = open(foutnhdr,'w')
#       fout.write(nhdrContent)
#       fout.close()

      #zip all the files together
      zipname = os.path.join(DTI_loc,prefix+'_'+suffix+'_DWI.zip')
      zipCmd = 'zip '+zipname + ' -mu '+dwi_list.replace(',',' ')+' '+dwi_list.replace('.nhdr','.raw.gz').replace(',',' ')+' '+b0_list.replace(',',' ')+' '+b0_list.replace('.nhdr','.raw.gz').replace(',',' ')
      print zipCmd
      os.system(zipCmd)

      
      
      




