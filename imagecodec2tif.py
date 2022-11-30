#!/usr/bin/env python3

#Copyright 2022 Andrew T. Dodd
#
#SPDX-License-Identifier: GPL-3.0-or-later

import imagecodecs
import tifffile
import sys
import os
import pyroexr
#import pyexiv2
import numpy as np
import argparse


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input', required=True,
    help='path to input file')

args = vars(ap.parse_args())
ap_name = ap.prog #TODO: Determine if we care about this, rawpy did it but we don't really need it.

filebase = os.path.splitext(args['input'])[0]
tifname = filebase + '.tif'

#FIXME:  Don't hardcode to linear sRGB/scRGB
icc_profile = imagecodecs.cms_profile('rgb', whitepoint=[0.3127,0.3290,1.0], primaries=[0.64, 0.33, 0.2126, 0.3, 0.6, 0.7152, 0.15, 0.06, 0.0722], gamma=1.0) #gamma requires patched imagecodecs as of November 2022, should be fixed next release

fileext = os.path.splitext(args['input'])[-1]

if(fileext == '.exr'):
    exrimage = pyroexr.load(args['input'])
    channels = exrimage.channels()
    #very much hardcoded to RGB, likely will fail for many other scenarios
    hdrimage = np.concatenate((channels['R'][:,:,np.newaxis], channels['G'][:,:,np.newaxis], channels['B'][:,:,np.newaxis]), axis=2)

else:
    hdrimage = imagecodecs.imread(args['input'])


#Discard alpha channel if present
hdrimage = hdrimage[:,:,0:3]

#Force to float32.  FIXME:  Allow downconverting to float16 to save size
hdrimage = hdrimage.astype(np.float32)

with tifffile.TiffWriter(tifname) as tif:
    tif.write(hdrimage,
            photometric='rgb',
            compression='zlib',
            predictor=True,
            extratags=[('InterColorProfile', tifffile.DATATYPE.BYTE, len(icc_profile), icc_profile)])

#with pyexiv2.Image(tifname) as exiv_image:
#    exiv_image.modify_icc(icc_profile)