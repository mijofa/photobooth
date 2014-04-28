#!/usr/bin/python

import sys
import gst
import time

count = 0

#jpeg = gst.element_factory_make ("jpegenc", "jpeg")
#jpeg.set_property ("quality", 100)

vl4src = gst.element_factory_make ("v4l2src", "source")
vl4src.set_property("device", "/dev/v4l/by-id/usb-046d_0825_6E2E6170-video-index0")

sink = gst.element_factory_make ("fakesink", "sink")

camerabin = gst.element_factory_make ("camerabin", "cam")
camerabin.set_property ("video-source", vl4src)
#camerabin.set_property ("image-encoder", jpeg)
camerabin.set_property ("viewfinder-sink", sink)
camerabin.set_property('image-capture-width', 1280)
camerabin.set_property('image-capture-height', 960)
camerabin.set_property('video-capture-width', 1024)
camerabin.set_property('video-capture-height', 576)

camerabin.set_state (gst.STATE_PLAYING)

def done(*args, **kwargs):
    sys.stdout.write('wtf')
#    print args, kwargs
#    print "Done."

camerabin.connect("image-done", done)

while True:
    filename = raw_input('Filename?')
    if filename == 'i' or filename == 'p':
        filename = "%d.png" % time.time()
    elif filename == 'm' or filename == 'v':
        filename = "%d.ogv" % time.time()
    if filename.endswith('png'):
        camerabin.set_property("mode", 0)
    if filename.endswith('ogv'):
        camerabin.set_property("mode", 1)
    camerabin.set_property("filename", filename)
    print "Capturing", filename,
    camerabin.emit("capture-start")
    if camerabin.get_property("mode") == 1:
        raw_input("Press Enter to stop.")
        camerabin.emit('capture-stop')

