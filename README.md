Various image conversion scripts

Intended as a combination of frontends to RawTherapee to support niche file formats and unsupported cameras prior to libraw integration into RT, and also in the case of libraw2dng as a base for
more advanced preprocessing scripts (such as average stacking)

imagecodec2tif was specifically designed to address the following RawTherapee issues:
https://github.com/Beep6581/RawTherapee/issues/6612
https://github.com/Beep6581/RawTherapee/issues/6606
https://github.com/Beep6581/RawTherapee/issues/1895

Currently depends on as-yet unreleased improvements/fixes in tifffile and imagecodecs as of November 2022.  All issues *should* be fixed as of the next tifffile and imagecodecs releases:

https://github.com/cgohlke/tifffile/issues/167
https://github.com/cgohlke/imagecodecs/pull/53