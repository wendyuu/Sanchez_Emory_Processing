#! /usr/bin/env python
# Script to generate the T1 and T2 atlas 
# from a set of skull stripped monkey brain images
#
# Yundi Shi

print 'Usage:\n\
BuildsMRIAtlas.py \n\
[\'all\' \'list\'(sAtlas_Subject_Prefix_List_[Age].txt)] \n\
[\'random\' (Random subject will be chosen t) \'template\'(atlas built from all subjects will be used)]\n\
[\'2weeks\' or/and \'3months\' or/and \'6months\'] \n\
-f [list_file]\n'

import os
import math
import fnmatch
import sys
from optparse import OptionParser

##########Parameters used for atlas building regarding subject selection##########
selection_mode = sys.argv[1];
template_mode = sys.argv[2];
# if no : All subjects are used in atlas building
# if yes: a list of subject will be used for atlas building
##################################################################################
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename",
                  help="read data from FILE", metavar="FILE")

if (selection_mode.lower() == 'list'):   
    if options.filename:
        print 'Reading input from file '+options.filename
        fname = options.filename;
    else:
        print 'Please specify the file that contains the list'
        prefixlist = args;
else:
   print 'Using all subjects listed in [age]_subjects.txt'

################################# List of tools used ##############################
from string import Template
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -i $file -o $file');
ThistmatchCmd = Template('/tools/bin_linux64/ImageMath $sou -matchHistogram $tar -outfile $out')
# tools to use to change the dof file to Atlaswerks compatible
Ttio1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransform.script $dof $txt')
TtioInv1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransformInv.script $dof $txt')
Ttio2Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/TransformCentered2NotCentered $txt $sou $tar $txt')
Ttio3Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/Double2FloatTransform.script $txt')
# Parameter files used in registration
parfile_NMI = os.path.join(ROOT_DIR,'processing/Reg_par_NMI.txt')
parfile_CC = os.path.join(ROOT_DIR,'processing/Reg_par_CC.txt')
parfile = parfile_CC


######################### DIRS ###################################
ROOT_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
OLD_COEMONKEY_TEMPLATE_DIR = '/primate/SanchezEmory/BrainDevYerkes/Template_CoeMonkeyFlu/'
sAtlasDir_parent = os.path.join(ROOT_DIR,'sMRIatlas');
template_name = Template('${sMRI}_template_allsubjects.gipl.gz')
template_parc_name = Template('template_parc.gipl.gz')
if (os.path.exists(sAtlasDir_parent)==False): os.system('mkdir '+sAtlasDir_parent);

# Loop through all the ages
for dir_tag in sys.argv[3:]:
    fname = dir_tag+'_subject.txt'
    print ('Now Processing the atlas of ' + dir_tag+' using the subjects listed in '+fname)
    prefixfile = os.path.join(ROOT_DIR,'processing',fname);
    prefixlist_f = open(prefixfile,'r');
    prefixlist=prefixlist_f.readlines();
    prefixlist_f.close()

    sAtlasDir_age = os.path.join(sAtlasDir_parent,dir_tag);
    if (os.path.exists(sAtlasDir_age)==False): os.mkdir(sAtlasDir_age)
    
    #parameters for AtlasWerks
    ###############################
    numiter = [100, 50, 40];
    alpha = [0.75, 0.75, 0.75];
    beta = [0.75, 0.75, 0.75];
    gamma = [0.1, 0.1, 0.1];
    maxPerturbation = [0.3, 0.2, 0.1];
    T1win = [0,60];
    T2win = [0,150];
    if (template_mode.lower() == 'template'):
	T1win = [0,160];
        T2win = [0,220];
    ##############################

    # Build T1 and T2 atlas
    for sMRI in ['T1','T2']:
        atlas_done = 0;
        sAtlasDir_sMRI = os.path.join(sAtlasDir_age,sMRI);
        if (os.path.exists(sAtlasDir_sMRI)==False): os.mkdir(sAtlasDir_sMRI)
    
        sAtlasDir_template = os.path.join(sAtlasDir_sMRI,'Areg2'+template_mode);
        if (os.path.exists(sAtlasDir_template)==False): os.mkdir(sAtlasDir_template)
    
        sAtlasDir = os.path.join(sAtlasDir_template,selection_mode+'_subjects');
        if (os.path.exists(sAtlasDir)==False): os.mkdir(sAtlasDir)
        
        print 'Atlas Building is done in ***'+sAtlasDir+'***'
        AtlasWerksfile = os.path.join(sAtlasDir,'sMRIAtlas_'+dir_tag+'_'+sMRI+'.xml')
        f = open(AtlasWerksfile,'w');
        
        #################################Directories######################################
        orig_dir = os.path.join(sAtlasDir_sMRI,'origImage');
        if(os.path.exists(orig_dir)==False): os.mkdir(orig_dir)
    
        avg_dir = os.path.join(sAtlasDir,'avgImage');
        if(os.path.exists(avg_dir)==False): os.mkdir(avg_dir)
        outAvg = os.path.join(avg_dir,dir_tag + '_avgImage_');

        atlas_dir = os.path.join(sAtlasDir,'sAtlas');
        if(os.path.exists(atlas_dir)==False): os.mkdir(atlas_dir)

        areg_dir_parent = os.path.join(sAtlasDir_template,'Areg');
        if(os.path.exists(areg_dir_parent)==False): os.mkdir(areg_dir_parent)

        histmatch_dir_parent = os.path.join(sAtlasDir_template,'HistMatched')
        if(os.path.exists(histmatch_dir_parent)==False): os.mkdir(histmatch_dir_parent)
        
        deformed_dir = os.path.join(sAtlasDir,'deformedImage');
        if(os.path.exists(deformed_dir)==False): os.mkdir(deformed_dir)
        outDeformed = os.path.join(deformed_dir,dir_tag + '_deformedImage_');
    
        Hfield_dir = os.path.join(sAtlasDir,'HField');
        if(os.path.exists(Hfield_dir)==False): os.mkdir(Hfield_dir)
        HField = os.path.join(Hfield_dir,dir_tag + '_fHField_');
        InvHField = os.path.join(Hfield_dir,dir_tag + '_iHField_');
        ##################################################################################
        
        tar = 1; # flag if the target of rigid body registration has been choosing
        sMRIlist = ' ';
        txtlist=' ';

        for line in prefixlist:	
            prefix = line[0:5];
            curr_loc =  os.path.join(ROOT_DIR,prefix,dir_tag);
            if os.path.exists(curr_loc): 
                SSDir = os.path.join(curr_loc,'sMRI','BM_EMS_SkullStripped');
	        #name of stripped T1s
                T1_ABC = os.path.join(SSDir,prefix+'_'+dir_tag+'_T1_050505mm_EMSStripped_Reg2T2.gipl.gz');
                if(os.path.exists(T1_EMS)==False):
                    T1_EMS = os.path.join(SSDir,prefix+'_'+dir_tag+'_T1_050505mm_EMSStripped_Reg205.gipl.gz');
                #name  stripped T2s
                T2_ABC = os.path.join(SSDir,prefix+'_'+dir_tag+'_T2_050510mm_EMSStripped_Reg2T2_RregT105.gipl.gz');
               
                if (template_mode.lower() == 'template' and tar == 1):
                    areg_tar_prefix = 'template'
                    print 'Using the pre-built Atlas as Affine registration template'
                    # areg to the template
                    areg_tar_T1 = os.path.join(OLD_COEMONKEY_TEMPLATE_DIR,template_name.substitute(sMRI='T1'))
                    areg_tar_T2 = os.path.join(OLD_COEMONKEY_TEMPLATE_DIR,template_name.substitute(sMRI='T1'))
                    # histmatched to one of the picked
                    histmatch_tar_T1 = T1_EMS
                    histmatch_tar_T2 = T2_EMS
                    histmatch_tar_prefix = prefix
                    tar = 0
                elif (tar == 1):
                    #pick the first one and affinely transform everyone to this one as initial
                    areg_tar_prefix = prefix
                    histmatch_tar_prefix = prefix
                    histmatch_tar_T1 = T1_EMS
                    histmatch_tar_T2 = T2_EMS
                    areg_tar_T1 = T1_EMS
                    areg_tar_T2 = T2_EMS
                    tar = 0
                    
                areg_dir = os.path.join(areg_dir_parent,'Areg2'+areg_tar_prefix)
                if(os.path.exists(areg_dir)==False): os.mkdir(areg_dir)
                histmatch_dir = os.path.join(histmatch_dir_parent,'Histmatched2'+histmatch_tar_prefix)
                if(os.path.exists(histmatch_dir)==False): os.mkdir(histmatch_dir)

                if(tar == 0):
                    sMRI_histmatched = eval(sMRI+'_EMS').replace('.gipl.gz','_Histmatched2'+histmatch_tar_prefix+'.gipl.gz').replace(SSDir,histmatch_dir)
                    sMRI_affine = eval(sMRI+'_EMS').replace('.gipl.gz','_IniAffine2'+areg_tar_prefix+'.gipl.gz').replace(SSDir,areg_dir)
                    
		    # Do affine transformation
                    dof = sMRI_affine.replace('.gipl.gz','.dof')
                    txt = sMRI_affine.replace('.gipl.gz','.txt')
                    if (os.path.exists(sMRI_histmatched) == False):
                        print 'Histogram Matching of '+eval(sMRI+'_EMS')+' to '+eval('histmatch_tar_'+sMRI)
                        histmatchCmd = ThistmatchCmd.substitute(sou=eval(sMRI+'_EMS'),tar=eval('histmatch_tar_'+sMRI),out=sMRI_histmatched)
                        os.system(histmatchCmd)
                    else:
                        print 'Histogram Matching of '+eval(sMRI+'_EMS')+' to '+eval('histmatch_tar_'+sMRI) + ' already done'
                    if (os.path.exists(dof) == False):
                        print 'Affinely transform '+sMRI_histmatched+' to '+eval('areg_tar_'+sMRI)
                        AregCmd = TaregCmd.substitute(tar=eval('areg_tar_'+sMRI),sou=sMRI_histmatched)+' -dofout '+dof+' -parin '+parfile+' -Tp 5 -p9'
                        os.system(AregCmd)
                        transformCmd = TtransformCmd.substitute(sou=eval(sMRI+'_EMS'),out=sMRI_affine,dofin = dof)+' -cspline'
                        os.system(transformCmd)
                    else:
                        print 'Affinely transform '+sMRI_histmatched+' to '+eval('areg_tar_'+sMRI)+' already done'    
                    # change dof to txt for atlaswerks to run
                    tio_cmd = Ttio1Cmd.substitute(txt=txt,dof=dof)
                    print tio_cmd
                    os.system(tio_cmd)
                    tio_cmd = Ttio2Cmd.substitute(txt=txt,sou=eval(sMRI+'_EMS'),tar=eval(sMRI+'_EMS'))
                    print tio_cmd
                    os.system(tio_cmd)
                    tio_cmd = Ttio3Cmd.substitute(txt=txt)
                    print tio_cmd
                    os.system(tio_cmd)
                    # affine initial reg included in atlaswerks
                    print template_name
                    # append the list
                    txtlist = txtlist + txt +' '
                    sMRIlist = sMRIlist + sMRI_histmatched + ' '
                        
        print sMRIlist
	AtlasWerksCmd = 'AtlasWerks' + sMRIlist + '--outputImageFilenamePrefix='+outAvg+sMRI+'_\
 --outputDeformedImageFilenamePrefix='+outDeformed+sMRI+'_\
 --outputHFieldFilenamePrefix='+HField+sMRI+'_\
 --outputHInvFieldFilenamePrefix='+InvHField+sMRI+'_'
	for slevel in [4, 2, 1]:
	    index = 2-int(math.log(slevel,2))
	    AtlasWerksCmd = AtlasWerksCmd + '\
 --scaleLevel='+str(slevel)+' --numberOfIterations='+str(numiter[index])+'\
 --alpha='+str(alpha[index])+'\
 --beta='+str(beta[index])+'\
 --gamma='+str(gamma[index])+'\
 --maxPerturbation='+str(maxPerturbation[index])
##  no window with histogram matching
##         if (sMRI == 'T1'):
## 	    AtlasWerksCmd = AtlasWerksCmd + '\
##  --intensityWindowMin='+str(T1win[0])+'\
##  --intensityWindowMax='+str(T1win[1])
## 	else:
## 	    AtlasWerksCmd = AtlasWerksCmd + '\
##  --intensityWindowMin='+str(T2win[0])+'\
##  --intensityWindowMax='+str(T2win[1])
        AtlasWerksCmd = AtlasWerksCmd +' '+txtlist
        
	print AtlasWerksCmd.replace(' ','\n')+'\n'+'\n'
 	f.write(AtlasWerksCmd.replace(' ','\n')+'\n'+'\n')
	AtlasWerkslog = os.path.join(atlas_dir,'sMRIAtlas_'+dir_tag+'_'+sMRI+'.log')
	os.system(AtlasWerksCmd+' 2>&1 |tee '+AtlasWerkslog)
        f.close()
        #adjust the intensiy level for the deformed images -- debug purpose
        for im in fnmatch.filter(os.listdir(deformed_dir),'*'+sMRI+'*_2*.mhd'):
            image = os.path.join(deformed_dir,im)
            adimg = image.replace('.mhd','_scaled.nrrd')
            os.system('ImageMath '+image+' -constOper 2,255 -outfile '+adimg)
            cmd = TunugzipCmd.substitute(file=adimg)
            print cmd
            os.system(cmd)
        #adjust the intensity level to get the final atlas
        for im in fnmatch.filter(os.listdir(avg_dir),'*'+sMRI+'*_2*.mhd'):
            image = os.path.join(avg_dir,im)
            sMRIAtlas = os.path.join(atlas_dir,sMRI+'_'+dir_tag+'_Atlas.nrrd')
            os.system('ImageMath '+image+' -constOper 2,255 -outfile '+adimg)
            cmd = TunugzipCmd.substitute(file=adimg)
            print cmd
            os.system(cmd)
        
        # propogate the parcellation
        # using b-spline registration to transform the old atlas to T1
        # store all the transformation in the processing folder
        processing_dir = os.path.join(atlas_dir,'parc_areg')
        if(os.path.exists(processing_dir)==False): os.system('mkdir '+processing_dir)
        dof = atlas.replace(atlas_dir,processing_dir).replace('.nrrd','_transformation.dof')

        if (os.path.exists(dof) == False):
            parfile = parfile_NMI_Bspline
            if (fnmatch.fnmatch(atlas,'*T1*')):
                # use CC for t1 to t1 registration
                parfile = parfile_CC_Bspline
                rregCmd = TrregCmd.substitute(tar=grid_template,sou=template_atlas)+' -dofout '+dof+' -parin '+parfile+' -Tp 5'
                os.system(rregCmd)
                aregCmd = TaregCmd.substitute(tar=grid_template,sou=template_atlas)+' -dofin '+dof+' -dofout '+dof+' -parin '+ parfile+' -Tp 5 -p9'
                os.system(aregCmd)

        # apply this transformation to the parcelletion
        # construct grid template

        # -------------IMPORTANT------------
        # the label files should NOT be interpolated linearly
        # Using nearest neighbour
        parc = atlas.replace('.nrrd','_parc.gipl.gz')
        transformCmd = TtransformCmd.substitute(sou=template_parc,out=parc,dofin = dof)+' -target '+grid_template
        if(os.path.exists(parc)==False):
            print transformCmd
            os.system(transformCmd)

        parc_vent = atlas.replace('.nrrd','_parc_vent.gipl.gz')
        if(os.path.exists(parc_vent)==False):
            transformCmd = TtransformCmd.substitute(sou=template_parc_vent,out=parc_vent,dofin = dof)+' -target '+grid_template
            print transformCmd
            os.system(transformCmd)
        os.remove(grid_template)

#         for parc in ['template','white','gray','csf','rest']:
#             if (os.path.exists(os.path.join(atlas_dir,parc+'.gipl'))==False):
#                 print 'Transforming'+parc+'.gipl'
#                 transformCmd = TtransformCmd.substitute(sou = atlasFile.replace('template',parc), out = newTemplate.replace('template',parc), dofin = dof) + ' -target ' + T1_RAI_gipl + ' -cspline'
#                 os.system(transformCmd)

