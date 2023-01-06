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

pyexiv2.enableBMFF()

#Lots of boilerplate code taken from rawpy's use_rawpy example here
ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input', nargs='+', type=argparse.FileType('rb'), required=True,
    help='path to input files')

args = vars(ap.parse_args())
ap_name = ap.prog #TODO: Determine if we care about this, rawpy did it but we don't really need it.

filecount = 0

for infile in args['input']:
    with rawpy.imread(infile) as raw:
        cfa_pattern = raw.raw_pattern.astype(np.uint8)
        bayer = raw.raw_image.astype('float64') # by default, astype makes a copy, so we should be safe here
        WB_AsShot = raw.camera_whitebalance
        WhiteLevel = raw.white_level
        WhiteLevel_perChannel = raw.camera_white_level_per_channel
        BlackLevel_perChannel = raw.black_level_per_channel
        CM_XYZ2camRGB = raw.rgb_xyz_matrix
        blacklevel_array = np.array(BlackLevel_perChannel)[cfa_pattern]
        filecount += 1

    #FIXME:  Detect if anything changes from file to file which should make us bomb out


    if not np.all(np.isin(cfa_pattern, [0,1,2,3])):
        print ('\n   *** Error ***\nCFA pattern contains non-RGB channels\n', ap_name, 'is terminated\n')
        exit()

    for i in range(blacklevel_array.shape[0]):
        for j in range(blacklevel_array.shape[1]):
            bayer[i::blacklevel_array.shape[0], j::blacklevel_array.shape[1]] -= blacklevel_array[i][j]

    #RT crashes badly if we preserve G1 as 3 instead of mapping it to 1.  TODO:  Check what DNG spec says about this.
    cfa_pattern[cfa_pattern == 3] = 1

    #FIXME:  Handle this better/more flexibly/more cleanly
    cmatrix = CM_XYZ2camRGB[:-1,:]

    if(filecount == 1):
        dng_data = bayer

        #FIXME:  Choose a better output filename than the first input raw file
        filebase = os.path.splitext(infile.name)[0]
        #FIXME:  This will clobber the first file if the input is a DNG...
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



        with pyexiv2.Image(infile.name) as exiv_file:
            exif_data = exiv_file.read_exif()
            preserved_data = {k: exif_data[k] for k in set(preserved_keys).intersection(exif_data.keys())}

    else:
        dng_data += bayer

dng_data /= filecount
avg_blacklevel = np.mean(BlackLevel_perChannel)
dng_data *= 65504/(WhiteLevel - avg_blacklevel)


#fugly, find a better solution for generating RATIONAL/SRATIONAL
def cm_to_flatrational(input_array):
    retarray = np.ones(input_array.size*2, dtype=np.int32)
    retarray[0::2] = (input_array.flatten()*10000).astype(np.int32)
    retarray[1::2] = 10000
    return retarray

print(cfa_pattern)
print(cfa_pattern.flatten())
#FIXME:  Save camera model into output so RT can detect appropriate DCP profile
dng_extratags = []
dng_extratags.append(('CFARepeatPatternDim', 'H', len(cfa_pattern.shape), cfa_pattern.shape, 0))
dng_extratags.append(('CFAPattern', 'B', cfa_pattern.size, cfa_pattern.flatten()))
dng_extratags.append(('ColorMatrix1', '2i', cmatrix.size, cm_to_flatrational(cmatrix)))
dng_extratags.append(('CalibrationIlluminant1', 'H', 1, 21)) #is there an enum for this in tifffile???
dng_extratags.append(('BlackLevelRepeatDim', 'H', 2, [1,1])) #BlackLevelRepeatDim
dng_extratags.append(('BlackLevel', 'H', 1, 0)) #BlackLevel - We subtracted black during processing, so it is 0
dng_extratags.append(('WhiteLevel', 'I', 1, 65504)) #WhiteLevel
dng_extratags.append(('DNGVersion', 'B', 4, [1,4,0,0])) #DNGVersion
dng_extratags.append(('DNGBackwardVersion', 'B', 4, [1,4,0,0])) #DNGBackwardVersion
dng_extratags.append(('AsShotNeutral', '2I', 3, np.array([WB_AsShot[1],WB_AsShot[0],WB_AsShot[1],WB_AsShot[1],WB_AsShot[1],WB_AsShot[2]], dtype=np.uint32))) #Normalize green channel to 1...  Not sure if libraw always uses 1024 as a reference for 1.0 in the white balance

with TIFF.TiffWriter(dngname) as dng:
    dng.write(dng_data.astype(np.float16),
            photometric='CFA',
            compression='zlib',
            predictor=34894, #floatingpointx2 predictor, currently requires patched tifffile to work properly until next tifffile release - November 2022
            #predictor=True,
            tile=(512,512), #RT does not like strips, save as tiles
            extratags=dng_extratags)

with pyexiv2.Image(dngname) as dng:
    dng.modify_exif(preserved_data)
