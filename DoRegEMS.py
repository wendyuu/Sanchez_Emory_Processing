#! /usr/bin/env python

# Script to run after skull stripping, atlas building and parcellation propogation
# 1) tissue segmentation using the newly build atlas
# 2) Apply affine registration (Nreg / RegisterImages) & Warp field to Parcellation
# 3) Apply affine registration (Nreg / RegisterImages) & Warp field to SubCortical Segmentation  
#
# Yundi Shi  
