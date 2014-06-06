#!/usr/bin/python
import kivy

from kivy.graphics.texture import Texture

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

#VIDEO_DEVICE = "/dev/v4l/by-id/usb-Vimicro_Corp._PC_Camera-video-index0" # Crappy camera
#VIDEO_DEVICE = "/dev/v4l/by-id/usb-046d_0825_6E2E6170-video-index0" # Good camera
VIDEO_DEVICE = "/dev/video{}"

## Seems CameraGStreamer got renamed between Kivy v1.6.0 and 1.8.0, this whole thing is a horrible hack anyway lets add more hackiness.
## I can't just reimport gst because that causes errors for some reason, so I need to set gst to the module already loaded in the kivy camera module.
try:
    import kivy.core.camera.camera_gstreamer
    CameraGst = kivy.core.camera.camera_gstreamer.CameraGStreamer
    gst = kivy.core.camera.camera_gstreamer.gst
except:
    import kivy.core.camera.camera_pygst
    CameraGst = kivy.core.camera.camera_pygst.CameraPyGst
    gst = kivy.core.camera.camera_pygst.gst
class CoreCamera(CameraGst):
    def init_camera(self):
        if self._pipeline:
            self._pipeline = None

        self._decodebin = gst.element_factory_make("v4l2src", "source")
        # I need to be able to specify the device path rather than just the /dev/video index, so I'm ignoring the index.
        self._decodebin.set_property("device", VIDEO_DEVICE.format(self._index))

        self._pipeline = gst.element_factory_make("camerabin", "decoder")

        self._pipeline.set_property("mode", 1)
        GL_CAPS = 'video/x-raw-rgb,red_mask=(int)0xff0000,' + \
                  'green_mask=(int)0x00ff00,blue_mask=(int)0x0000ff'

        self._camerasink = gst.element_factory_make("appsink", "camerasink")
        self._camerasink.set_property("emit-signals", True)
        self._camerasink.set_property("caps", gst.Caps(GL_CAPS))
        self._pipeline.set_property("video-source", self._decodebin)
        self._pipeline.set_property("viewfinder-sink", self._camerasink)

        self._camerasink.connect('new-buffer', self._gst_new_buffer)

        self.start()
        if self._camerasink and not self.stopped:
            self.start()
    def _copy_to_gpu(self):
        for i in self._camerasink.sink_pads():
            print i.get_negotiated_caps()
        '''Copy the the buffer into the texture'''
        if self._texture is None:
            Logger.debug('Camera: copy_to_gpu() failed, _texture is None !')
            return
        self._texture.blit_buffer(self._buffer, colorfmt=self._format) # Commenting this line makes the app not crash, but it leaves the uix.Camera widget blank.
        self._buffer = None
        self.dispatch('on_texture')
kivy.core.camera.Camera = CoreCamera
from kivy.uix.camera import Camera

class Main(App):
    def f(self, *args):
        print self.cam._camera._pipeline
        return
        if not self.rec:
            self.rec = True
            print self.cam._camera._pipeline.set_property("filename", '/tmp/test-vid.ogv')
            print self.cam._camera._pipeline.emit("capture-start")
        else:
            print self.cam._camera._pipeline.emit("capture-stop")
    def build(self):
        self.rec = False
        self.root = FloatLayout()
        self.cam = Camera(index=0, resolution=(1280,960), play=True, stopped=False)
        self.cam.pos_hint['center'] = [0.5,0.5]
        self.root.add_widget(self.cam)
#        btn = Button(size_hint=[0.33, 0.1], on_press=self.f,
#                pos_hint={'top': 0.1, 'left': '0'},
#                text="Foo",
#                background_color=[0,0,1,1],
#            )
#        self.root.add_widget(btn)
        return self.root

Main().run()
