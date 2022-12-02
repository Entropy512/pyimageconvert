#!/usr/bin/env python3

#Copyright 2022 Andrew T. Dodd
#
#SPDX-License-Identifier: GPL-3.0-or-later

import tifffile as TIFF
import rawpy
from pathlib import Path
import numpy as np
import argparse
import os
import pyexiv2

#Lots of boilerplate code taken from rawpy's use_rawpy example here
ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input', required=True,
    help='path to input file')

args = vars(ap.parse_args())
ap_name = ap.prog #TODO: Determine if we care about this, rawpy did it but we don't really need it.

filebase = os.path.splitext(args['input'])[0]
dngname = filebase + '.dng'

preserved_keys = ['Exif.Photo.LensModel',
                'Exif.Photo.LensModel',
                'Exif.Photo.FocalLengthIn35mmFilm',
                'Exif.Photo.FocalLength',
                'Exif.Photo.FNumber',
                'Exif.Photo.ExposureTime',
                'Exif.Image.Make',
                'Exif.Image.Model',
                'Exif.Image.Orientation',
                'Exif.Image.DateTime',
                'Exif.Sony2.SonyModelID', #not sure if we want to keep this?
                'Exif.Sony2.LensID', #needed for RT to get lens data
                'Exif.Photo.ISOSpeedRatings']

with rawpy.imread(args['input']) as raw:
    bayer_pattern = raw.raw_pattern
    bayer = raw.raw_image_visible.astype('float64') # by default, astype makes a copy, so we should be safe here
    WB_AsShot = raw.camera_whitebalance
    WhiteLevel = raw.white_level
    WhiteLevel_perChannel = raw.camera_white_level_per_channel
    BlackLevel_perChannel = raw.black_level_per_channel
    CM_XYZ2camRGB = raw.rgb_xyz_matrix

with pyexiv2.Image(args['input']) as exiv_file:
    exif_data = exiv_file.read_exif()
    preserved_data = {k: exif_data[k] for k in set(preserved_keys).intersection(exif_data.keys())}

#FIXME:  Handle X-Trans somehow.  Low priority since I don't own an x-trans camera and likely never will
if bayer_pattern.shape != (2,2):
    print ('\n   *** Error ***\nBayer pattern isn\'t 2 by 2\n', ap_name, 'is terminated\n')
    exit()

if not np.all(np.isin([0,1,2,3], bayer_pattern)):
    print ('\n   *** Error ***\nBayer pattern contains non-RGB channels\n', ap_name, 'is terminated\n')
    exit()

iRrow,  iRclmn  = np.argwhere(bayer_pattern == 0)[0]
iG0row, iG0clmn = np.argwhere(bayer_pattern == 1)[0]
iBrow,  iBclmn  = np.argwhere(bayer_pattern == 2)[0]
iG1row, iG1clmn = np.argwhere(bayer_pattern == 3)[0]
 
bayer[ iRrow::2,  iRclmn::2] -= BlackLevel_perChannel[0]
bayer[iG0row::2, iG0clmn::2] -= BlackLevel_perChannel[1]
bayer[ iBrow::2,  iBclmn::2] -= BlackLevel_perChannel[2]
bayer[iG1row::2, iG1clmn::2] -= BlackLevel_perChannel[3]

bayer *= 65504/WhiteLevel

#RT crashes badly if we preserve G1 as 3 instead of mapping it to 1.  TODO:  Check what DNG spec says about this.
bayer_pattern[bayer_pattern == 3] = 1

#FIXME:  Handle this better/more flexibly/more cleanly
cmatrix = CM_XYZ2camRGB[:-1,:]

#fugly, find a better solution for generating RATIONAL/SRATIONAL
def cm_to_flatrational(input_array):
    retarray = np.ones(input_array.size*2, dtype=np.int32)
    retarray[0::2] = (input_array.flatten()*10000).astype(np.int32)
    retarray[1::2] = 10000
    return retarray

#FIXME:  Save camera model into output so RT can detect appropriate DCP profile
dng_extratags = []
dng_extratags.append(('CFARepeatPatternDim', 'H', len(bayer_pattern.shape), bayer_pattern.shape, 0))
dng_extratags.append(('CFAPattern', 'B', bayer_pattern.size, bayer_pattern.flatten()))
dng_extratags.append(('ColorMatrix1', '2i', cmatrix.size, cm_to_flatrational(cmatrix)))
dng_extratags.append(('CalibrationIlluminant1', 'H', 1, 21)) #is there an enum for this in tifffile???
dng_extratags.append(('BlackLevelRepeatDim', 'H', 2, [1,1])) #BlackLevelRepeatDim
dng_extratags.append(('BlackLevel', 'H', 1, 0)) #BlackLevel - We subtracted black during processing, so it is 0
dng_extratags.append(('WhiteLevel', 'I', 1, 65504)) #WhiteLevel
dng_extratags.append(('DNGVersion', 'B', 4, [1,4,0,0])) #DNGVersion
dng_extratags.append(('DNGBackwardVersion', 'B', 4, [1,4,0,0])) #DNGBackwardVersion
dng_extratags.append(('AsShotNeutral', '2I', 3, np.array([WB_AsShot[1],WB_AsShot[0],WB_AsShot[1],WB_AsShot[1],WB_AsShot[1],WB_AsShot[2]], dtype=np.uint32))) #Normalize green channel to 1...  Not sure if libraw always uses 1024 as a reference for 1.0 in the white balance

with TIFF.TiffWriter(dngname) as dng:
    dng.write(bayer.astype(np.float16),
            photometric='CFA',
            compression='zlib',
            predictor=34894, #floatingpointx2 predictor, currently requires patched tifffile to work properly until next tifffile release - November 2022
            #predictor=True,
            tile=(512,512), #RT does not like strips, save as tiles
            extratags=dng_extratags)

with pyexiv2.Image(dngname) as dng:
    dng.modify_exif(preserved_data)
