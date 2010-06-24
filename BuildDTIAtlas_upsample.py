#! /usr/bin/env python
# Script to generate the DTI atlas using normaized FA 
# from a set of skull stripped monkey brain images
#
# Yundi Shi

print 'Usage:\n\
BuildsMRIAtlas.py \n\
[\'all\' \'list\'(DTIAtlas_Subject_Prefix_List_[Age].txt)] \n\
[\'random\' (Random subject will be chosen t) \'template\'(atlas built from all subjects will be used)]\n\
[\'normFA\' \'curvFA\'] \n\
[\'2weeks\' or/and \'3months\' or/and \'6months\] \n'

import os
import math
import fnmatch
import sys

##########Parameters used for atlas building regarding subject selection##########
selection_mode = sys.argv[1];
template_mode = sys.argv[2];
DTI = sys.argv[3];
# if no : All subjects are used in atlas building
# if yes: a list of subject will be used for atlas building
##################################################################################

from string import Template
TaregCmd = Template('/tools/rview_linux64_2008/areg $tar $sou')
TtransformCmd = Template('/tools/rview_linux64_2008/transformation $sou $out -dofin $dofin')
TconvCmd = Template('/tools/bin_linux64/convertITKformats $infile $outfile')
TunucvtCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu convert -i $infile -t float| /tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -o $outfile');
TunugzipCmd = Template('/tools/Slicer3/Slicer3-3.4.1-2009-10-09-linux-x86_64/bin/unu save -f nrrd -e gzip -i $file -o $file');
TImageMathcvtCmd = Template('/tools/bin_linux64/ImageMath $infile -constOper 0,0 -outfile $outfile');
ThistmatchCmd = Template('/tools/bin_linux64/ImageMath $sou -matchHistogram $tar -outfile $out')
Ttio1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransform.script $dof $txt')
TtioInv1Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/dof2itkTransformInv.script $dof $txt')
Ttio2Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/TransformCentered2NotCentered $txt $sou $tar $txt')
Ttio3Cmd = Template('/primate/SanchezEmory/BrainDevYerkes/processing/Double2FloatTransform.script $txtin $txtout')
TcurvCmd = Template('/tools/bin_linux64/maxcurvature $FA -o $curvFA')
#TCenterImage = Template('/primate/SanchezEmory/BrainDevYerkes/processing/ChangeOrigin.py $infile $outfile')
TChangeSpaceDir = Template('/primate/SanchezEmory/BrainDevYerkes/processing/ChangeSpaceDir.py $infile $outfile')
THfieldFixUp = Template('/primate/SanchezEmory/BrainDevYerkes/processing/HfieldFixUp.py $Hfield $Img')
ORIG_DATA_DIR = '/primate/SanchezEmory/BrainDevYerkes/'
Template_Dir = '/primate/SanchezEmory/BrainDevYerkes/Template_CoeMonkeyFlu/'
DTIprocess = '/tools/bin_linux64/dtiprocess'
DTIaverage = '/tools/bin_linux64/dtiaverage'
ResampleDTI = '/home/budin/LocalWork/ResampleDTIlogEuclidean-linux64/ResampleDTIlogEuclidean -p -23 -n 4'

# parameters for affine transformation
parfile_NMI = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_NMI.txt')
parfile_CC = os.path.join(ORIG_DATA_DIR,'processing/Reg_par_CC.txt')
parfile = parfile_CC

DTIAtlasDir_parent = os.path.join(ORIG_DATA_DIR,'DTIAtlas_Upsampled');
if (os.path.exists(DTIAtlasDir_parent)==False): os.system('mkdir '+DTIAtlasDir_parent);

# subjects used for atlas building -- LISTED IN A FILE or ALL

for dir_tag in sys.argv[4:]:
    print ('Now Processing the atlas of ' + dir_tag)
    if (selection_mode.lower() == 'list'):   
        prefixlist = open(os.path.join(ORIG_DATA_DIR, 'processing/DTIAtlas_Subject_Prefix_List_'+dir_tag+'.txt'),'r');
        print 'Using Subjects as stored in processing/DTIAtlas_Subject_Prefix_List_'+dir_tag+'.txt'
    else:
        prefixlist_f = open(os.path.join(ORIG_DATA_DIR, 'processing/'+dir_tag+'_subject.txt'),'r');  
        prefixlist = prefixlist_f.readlines();
        prefixlist_f.close()

    DTIAtlasDir_age = os.path.join(DTIAtlasDir_parent,dir_tag);
    if (os.path.exists(DTIAtlasDir_age)==False): os.mkdir(DTIAtlasDir_age)

    DTIAtlasDir_DTI = os.path.join(DTIAtlasDir_age,DTI);
    if (os.path.exists(DTIAtlasDir_DTI)==False): os.mkdir(DTIAtlasDir_DTI)
    
    DTIAtlasDir_template = os.path.join(DTIAtlasDir_DTI,'Areg2'+template_mode);
    if (os.path.exists(DTIAtlasDir_template)==False): os.mkdir(DTIAtlasDir_template)
    
    DTIAtlasDir = os.path.join(DTIAtlasDir_template,selection_mode+'_subjects');
    if (os.path.exists(DTIAtlasDir)==False): os.mkdir(DTIAtlasDir)

    print 'Atlas Building is done in ***'+DTIAtlasDir+'***'
    AtlasWerksfile = os.path.join(DTIAtlasDir,'DTIAtlas_'+dir_tag+'.xml')
    f = open(AtlasWerksfile,'w');   

    #parameters for AtlasWerks
    ###############################
    # 6months parameters
    numiter = [100, 50, 40];
    alpha = [0.5, 0.5, 0.2];
    beta = [0.5, 0.5, 0.2];
    gamma = [0.1, 0.1, 0.05];
    maxPerturbation = [0.2, 0.1, 0.1];
    FAwin = [10, 120]
    ## numiter = [500, 200];
##     alpha = [0.1, 0.1];
##     beta = [0.1, 0.1];
##     gamma = [0.01, 0.01];
##     maxPerturbation = [0.2, 0.1];
    ###############################
    
    #################################Directories######################################
    orig_dir = os.path.join(DTIAtlasDir_age,'origImage');
    if(os.path.exists(orig_dir)==False): os.mkdir(orig_dir)
    
    avg_dir = os.path.join(DTIAtlasDir,'avgImage');
    if(os.path.exists(avg_dir)==False): os.mkdir(avg_dir)
    outAvg = os.path.join(avg_dir,dir_tag + '_avgImage_');

    atlas_dir = os.path.join(DTIAtlasDir,'DTIAtlas');
    if(os.path.exists(atlas_dir)==False): os.mkdir(atlas_dir)

    areg_dir_parent = os.path.join(DTIAtlasDir_template,'Areg');
    if(os.path.exists(areg_dir_parent)==False): os.mkdir(areg_dir_parent)

    warp_dir = os.path.join(DTIAtlasDir,'WarpedDTI');
    if(os.path.exists(warp_dir)==False): os.mkdir(warp_dir)

    histmatch_dir_parent = os.path.join(DTIAtlasDir_template,'HistMatched')
    curv_dir = os.path.join(DTIAtlasDir_DTI,'OrigcurvFA')
    if(DTI.lower()=='curvfa'):
        if(os.path.exists(curv_dir)==False): os.mkdir(curv_dir)
    elif(DTI.lower()=='normfa'):
        if(os.path.exists(histmatch_dir_parent)==False): os.mkdir(histmatch_dir_parent)
                
    deformed_dir = os.path.join(DTIAtlasDir,'deformedImage');
    if(os.path.exists(deformed_dir)==False): os.mkdir(deformed_dir)
    outDeformed = os.path.join(deformed_dir,dir_tag + '_deformedImage_');
    
    Hfield_dir = os.path.join(DTIAtlasDir,'HField');
    if(os.path.exists(Hfield_dir)==False): os.mkdir(Hfield_dir)
    HField = os.path.join(Hfield_dir,dir_tag + '_fHField_');
    InvHField = os.path.join(Hfield_dir,dir_tag + '_iHField_');
    ##################################################################################
    
    ##################Preparation before affine registration##########################
    DTIlist = ' ';
    tensorlist = ' ';
    txtlist = ' ';
    tar_flag = 1; # flag to show if the target is picked
    for line in prefixlist:	
        prefix = line[0:5];
	curr_loc =  os.path.join(ORIG_DATA_DIR,prefix,dir_tag);
	if os.path.exists(curr_loc): 
	   DTIDir = os.path.join(curr_loc,'DTI');
           # generate FA(0-255)
           print DTIDir
           for file in fnmatch.filter(os.listdir(DTIDir),'FA_*B0_upsampled.nrrd'):
               FA_nrrd = os.path.join(DTIDir,file);
               FA_center = FA_nrrd.replace(DTIDir,orig_dir).replace('.nrrd','_center.nrrd');
               TENSOR_nrrd = FA_nrrd.replace('FA','TENSOR');
               TENSOR_center = TENSOR_nrrd.replace(DTIDir,orig_dir).replace('.nrrd','_center.nrrd');
               DWI_nrrd = FA_nrrd.replace('FA_','');
               DWI_center = DWI_nrrd.replace(DTIDir,orig_dir).replace('.nrrd','_center.nrrd');
               #Center the FA and DWI and change the measurement frame of TENSOR;
               if(os.path.exists(DWI_center)==False):
                   ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=DWI_nrrd,outfile=DWI_center)+' --dwi'
                   print ChangeSpaceDirCmd
                   os.system(ChangeSpaceDirCmd)
               if(os.path.exists(FA_center)==False):
                   ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=FA_nrrd,outfile=FA_center)
                   print ChangeSpaceDirCmd
                   os.system(ChangeSpaceDirCmd)
               if(os.path.exists(TENSOR_center)==False):
                   ChangeSpaceDirCmd = TChangeSpaceDir.substitute(infile=TENSOR_nrrd,outfile=TENSOR_center)+' --tensor'
                   print ChangeSpaceDirCmd
                   os.system(ChangeSpaceDirCmd)
               FA = FA_center.replace('nrrd','gipl.gz')
               convCmd = TconvCmd.substitute(infile=FA_center,outfile=FA)+' -float 255';
               os.system(convCmd)    
           # normFA or curvFA
           if(DTI.lower() == 'normfa'):
               sou = 'FA_histmatched';
               tar = 'FA_tar'
               # target for areg and histmatch
               if (tar_flag == 1):
                   if(template_mode.lower() == 'template'):
                       tar_prefix = 'template';
                       print 'Using the pre-built Atlas as Affine registration template'
                       FA_tar = os.path.join(Template_Dir,'FA_template.gipl.gz');
                   else:  #pick the first one and affinely transform everyone to this one as initial
                       tar_prefix = prefix;
                       FA_tar = FA;
                   histmatch_dir = os.path.join(histmatch_dir_parent,'Histmatch2'+tar_prefix);
                   if(os.path.exists(histmatch_dir)==False): os.mkdir(histmatch_dir)    
                   areg_dir = os.path.join(areg_dir_parent,'Areg2'+tar_prefix);
                   if(os.path.exists(areg_dir)==False): os.mkdir(areg_dir)
                   tar_flag = 0;
               # generating normFA
               FA_histmatched = FA.replace('.gipl.gz','_Histmatched2'+tar_prefix+'.gipl.gz').replace(orig_dir,histmatch_dir);
               if (os.path.exists(FA_histmatched) == False):
		   print 'Histogram Matching of '+FA+' to '+FA_tar
		   histmatchCmd = ThistmatchCmd.substitute(sou=FA,tar=FA_tar,out=FA_histmatched);
		   os.system(histmatchCmd)
               affine_tar = FA.replace('.gipl.gz','_IniAffine2'+tar_prefix+'.gipl.gz').replace(orig_dir,areg_dir);
           elif(DTI.lower() == 'curvfa'):
               sou = 'curvFA';
               tar = 'curvFA_tar';
               # generating curvature FA
               curvFA = FA.replace('FA','curvFA').replace(orig_dir,curv_dir);
               if (os.path.exists(curvFA)==False):
                   curvCmd = TcurvCmd.substitute(FA=FA,curvFA=curvFA) + ' -s 1.0';
                   print curvCmd
                   os.system(curvCmd)
               # target for affine transformation
               if(tar_flag == 1):
                   if (template_mode.lower() == 'template'):
                       tar_prefix = 'template';
                       print 'Using the pre-built Atlas as Affine registration template'
                       FA_tar = os.path.join(Template_Dir,'FA_template.gipl.gz');
                       curvFA_tar = os.path.join(Template_Dir,'curvFA_template.gipl.gz');
                       if(os.path.exists(curvFA_tar)==False):
                           curvCmd = TcurvCmd.substitute(FA=FA_tar,curvFA=curvFA_tar)+' -s 0.5';
                           print curvCmd
                           os.system(curvCmd)
                   else: #pick the first one and affinely transform everyone to this one as initial
                       tar_prefix = prefix;
                       curvFA_tar = curvFA;
                   # areg_dir target specific
                   areg_dir = os.path.join(areg_dir_parent,'Areg2'+tar_prefix);
                   if(os.path.exists(areg_dir)==False): os.mkdir(areg_dir)
                   tar_flag = 0
               affine_tar = curvFA.replace('.gipl','_IniAffine2'+tar_prefix+'.gipl.gz').replace(curv_dir,areg_dir);
    
           # Do affine transformation        
           dof = affine_tar.replace('.gipl.gz','.dof')
           txt = affine_tar.replace('.gipl.gz','_float.txt')
           txt_double = affine_tar.replace('.gipl.gz','_double.txt')
           dti_affine_sou = FA_center.replace('FA','TENSOR');
           FA_affine_tar = FA_center.replace(orig_dir,areg_dir).replace('.nrrd','_IniAffine2'+tar_prefix+'.nrrd');
           dti_affine_tar = dti_affine_sou.replace(orig_dir,areg_dir).replace('.nrrd','_IniAffine2'+tar_prefix+'.nrrd');
           # affine registration
           if (os.path.exists(dof) == False):
               print 'Affinely register '+eval(sou)+' to '+eval(tar);
               AregCmd = TaregCmd.substitute(tar=eval(tar),sou=eval(sou))+' -dofout '+dof+' -parin '+parfile+' -p9 -Tp 5';
               os.system(AregCmd)
           # change dof to txt for atlaswerks to run
           tio_cmd = Ttio1Cmd.substitute(txt=txt_double,dof=dof)
#           print tio_cmd
           os.system(tio_cmd)
           tio_cmd = Ttio2Cmd.substitute(txt=txt_double,sou=eval(sou),tar=eval(sou))
           print tio_cmd
           os.system(tio_cmd)
           tio_cmd = Ttio3Cmd.substitute(txtin=txt_double,txtout=txt)
#           print tio_cmd
           os.system(tio_cmd)
           # transformation
           if(os.path.exists(dti_affine_tar) == False):
              print 'Transform tensor based on this affine registration ****FOR GABE****'
              ResampleDTI_cmd = ResampleDTI+' '+ dti_affine_sou+' ' +dti_affine_tar+' -f '+txt_double
              print ResampleDTI_cmd
              os.system(ResampleDTI_cmd)
              dtiprocess_cmd = DTIprocess+' '+ dti_affine_tar+' -f '+FA_affine_tar
              print dtiprocess_cmd
              os.system(dtiprocess_cmd)
##               transformCmd = TtransformCmd.substitute(sou=eval(sou),out=affine_tar,dofin = dof)+' -cspline';
##               os.system(transformCmd)
           # subjects included in atlaswerks
           DTIlist = DTIlist + eval(sou) + ' ';
           # affine initial reg included in atlaswerks
           txtlist = txtlist + txt +' ';
           # tensors used in warping afterwards
           tensorlist = tensorlist +dti_affine_sou +' '
   
           print DTIlist
    AtlasWerksCmd = 'AtlasWerks' + DTIlist + '--outputImageFilenamePrefix='+outAvg+DTI+'_\
 --outputDeformedImageFilenamePrefix='+outDeformed+DTI+'_\
 --outputHFieldFilenamePrefix='+HField+DTI+'_'
# --outputHInvFieldFilenamePrefix='+InvHField+DTI+'_'
    for slevel in [4, 2, 1]:
        index = 2-int(math.log(slevel,2));
        AtlasWerksCmd = AtlasWerksCmd + '\
 --scaleLevel='+str(slevel)+' --numberOfIterations='+str(numiter[index])+'\
 --alpha='+str(alpha[index])+'\
 --beta='+str(beta[index])+'\
 --gamma='+str(gamma[index])+'\
 --maxPerturbation='+str(maxPerturbation[index])
    AtlasWerksCmd = AtlasWerksCmd +'\
 --intensityWindowMin='+str(FAwin[0])+'\
 --intensityWindowMax='+str(FAwin[1])
    AtlasWerksCmd = AtlasWerksCmd +' '+txtlist;

    print AtlasWerksCmd.replace(' ','\n')+'\n'+'\n'
    f.write(AtlasWerksCmd.replace(' ','\n')+'\n'+'\n');
    AtlasWerkslog = os.path.join(DTIAtlasDir,'DTIAtlas_'+dir_tag+'_'+DTI+'.log')

    if(os.path.exists(AtlasWerkslog)==False):
        os.system(AtlasWerksCmd+' 2>&1 |tee '+AtlasWerkslog)
    else:
        print 'Log Exists for AtlasWerks... won\'t rerun'
        
    #adjust the intensity level
    for im in fnmatch.filter(os.listdir(avg_dir),'*'+DTI+'*.raw'):
            image = os.path.join(avg_dir,im);
            adimg = image.replace('.raw','_scaled.nrrd')
            convCmd = TconvCmd.substitute(infile=image.replace('.raw','.mhd'),outfile=adimg)+' -float 255';
            os.system(convCmd)
            os.remove(image)
            os.remove(image.replace('.raw','.mhd'))
            os.system(TunugzipCmd.substitute(file=adimg));
    for im in fnmatch.filter(os.listdir(deformed_dir),'*2_????.raw'):
	    image = os.path.join(deformed_dir,im);
            adimg = image.replace('.raw','_scaled.nrrd')
            convCmd = TconvCmd.substitute(infile=image.replace('.raw','.mhd'),outfile=adimg)+' -float 255';
            os.system(convCmd)
            os.remove(image)
            os.remove(image.replace('.raw','.mhd'))
            os.system(TunugzipCmd.substitute(file=adimg));
    
    #Calculate tensor atlas
    counter = 0;
    avgtensorlist_resampdti = '';
    avgtensorlist_dtiproc = ''
    print DTIlist
    for img in tensorlist.split():
	    dti_sou = img;
            #for debugging
            dti_tar_dtiproc = dti_sou.replace('.nrrd','_Warped_Using'+DTI+'_dtiproc.nrrd').replace(orig_dir,warp_dir);
            dti_tar_resampdti = dti_sou.replace('.nrrd','_Warped_Using'+DTI+'_resampdti.nrrd').replace(orig_dir,warp_dir);
            F_hfield = os.path.join(Hfield_dir,dir_tag+'_fHField_'+DTI+'_'+"%04d"%counter+'.mhd')
                                             
            if(os.path.exists(dti_tar_dtiproc)==False):
                # for debugging
                #dtiprocess changes the space directions which is not supposed to happen
                dtiprocess_cmd = DTIprocess+' '+ dti_sou+' -w '+dti_tar_dtiproc+' -F '+F_hfield + ' --h-field -i linear'
                print '\n'+dtiprocess_cmd+'\n'
                os.system(dtiprocess_cmd)
                print TunugzipCmd.substitute(file=dti_tar_dtiproc)
                os.system(TunugzipCmd.substitute(file=dti_tar_dtiproc));
                FA = dti_tar_dtiproc.replace('.nrrd','_FA.nrrd');
                if(os.path.exists(FA)==False):
                    dtiprocess_cmd = DTIprocess+' '+dti_tar_dtiproc+' -f '+FA
                    print dtiprocess_cmd
                    os.system(dtiprocess_cmd)
            if(os.path.exists(dti_tar_resampdti)==False):
                ResampleDTI_cmd = ResampleDTI+' '+ dti_sou+' ' +dti_tar_resampdti+' -H '+F_hfield +' --log'
                print '\n'+ResampleDTI_cmd+'\n'
                os.system(ResampleDTI_cmd)
                
                print TunugzipCmd.substitute(file=dti_tar_resampdti)
                os.system(TunugzipCmd.substitute(file=dti_tar_resampdti));
                
                FA = dti_tar_resampdti.replace('.nrrd','_FA.nrrd');
                if(os.path.exists(FA)==False):
                    dtiprocess_cmd = DTIprocess+' '+dti_tar_resampdti+' -f '+FA
                    print dtiprocess_cmd
                    os.system(dtiprocess_cmd)
            #gzip the mhd field
            gzipCmd = 'gzip '+F_hfield.replace('.mhd','.raw') + ' -f';
            print gzipCmd
            os.system(gzipCmd)
    
            avgtensorlist_resampdti = avgtensorlist_resampdti + ' '+dti_tar_resampdti;
            avgtensorlist_dtiproc = avgtensorlist_dtiproc + ' '+dti_tar_dtiproc;
            counter = counter + 1;

    for method in ['resampdti','dtiproc']:
        tensoratlas = os.path.join(atlas_dir,'DTIAtlas_'+dir_tag+'_w_'+selection_mode+'subjectsAreg2'+template_mode+'Using'+DTI+'With'+method+'.nrrd')
        cFA = tensoratlas.replace('.nrrd','_cFA.nrrd')
        FA = tensoratlas.replace('.nrrd','_FA.nrrd');
        MD = tensoratlas.replace('.nrrd','_MD.nrrd');
        dtiavg_cmd = DTIaverage+' ' + tensoratlas + eval('avgtensorlist_'+method)
        print dtiavg_cmd
        os.system(dtiavg_cmd)
        #convert tensor to float format for slicer3
        unucvtCmd = TunucvtCmd.substitute(infile=tensoratlas,outfile=tensoratlas.replace('.nrrd','_float.nrrd'))
        print unucvtCmd
        os.system(unucvtCmd)
        dtiprocess_cmd = DTIprocess+' '+tensoratlas+' -f '+FA+' -m '+ MD +' -c '+cFA
        print dtiprocess_cmd
        os.system(dtiprocess_cmd)
        print TunugzipCmd.substitute(file=tensoratlas)
        os.system(TunugzipCmd.substitute(file=tensoratlas));
f.close();
