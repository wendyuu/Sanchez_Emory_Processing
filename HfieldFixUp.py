#! /usr/bin/env python
# Change space direction of HField to Img, convert it to gzip nrrd and delete the mhd and raw
# Yundi Shi

import os
import math
import fnmatch
import sys
import shutil
from optparse import OptionParser
parser = OptionParser()
(options, args) = parser.parse_args()

from string import Template
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
unuhead = '/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu head '

if(len(args)<2):
    print 'Usage: HfieldFixUp.py [Hfield] [Img]'
    print 'Change space direction of HField to Img. Convert it to gzip nrrd and delete the mhd and raw'
else:
    Hfield = sys.argv[1];
    Img = sys.argv[2];
    print 'Change Space Direction of Hfield '+Hfield+' to the Image '+Img +' and convert it to nrrd' 

    # convert mhd to nrrd and delete mhd and raw
    if fnmatch.fnmatch(Hfield,'*.mhd'):
        Hfield_nrrd = Hfield.replace('.mhd','.nrrd');
        cvtCmd = TconvCmd.substitute(infile=Hfield,outfile=Hfield_nrrd);
        print cvtCmd
        os.system(cvtCmd)
#        os.remove(Hfield)
#        os.remove(Hfield.replace('.mhd','.raw'))
    else :
        Hfield_nrrd = Hfield

    # read in the space direction form the image file
    nhdrContent = os.popen(unuhead+Img).read();
    space_dir = fnmatch.filter(nhdrContent.split('\n'),'space directions:*')[0].replace('none ','');

    f_nrrd = open(Hfield_nrrd,'r')
    content = '';
    for line in f_nrrd.readlines():
        if(fnmatch.fnmatch(line,'space directions*')):
            print 'Replacing '+line+' with '+space_dir
            content = content + space_dir + '\n'
        else:
            content = content + line;
    print content[1:500]
    f_nrrd.close()
    f_nrrd = open(Hfield_nrrd,'w')
    f_nrrd.write(content)
    
           


                                                             
                                   

                                                        
