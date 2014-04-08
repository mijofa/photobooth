#!/usr/bin/python
import kivy
kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout

import time

### Mirror the camera widget
## Source: https://gist.github.com/alanctkc/c59ca9fd83fff6259289
## I believe the 2 Translate sections could be replaced with setting the origin key in the Rotate section, but that can't be done in version 1.6.0
Builder.load_string("""
<MirrorCamera>
    canvas.before:
        PushMatrix
        Translate:
            xy: (self.x + self.width / 2, self.y + self.height / 2)
        Rotate:
            angle: 180
            axis: (0, 0, 1.0)
        Translate:
            xy: (-self.x - self.width / 2, -self.y - self.height / 2)
    canvas.after:
        PopMatrix

""")
class MirrorCamera(Camera):
    def _camera_loaded(self, *largs):
        self.texture = self._camera.texture
        self.texture_size = list(self.texture.size)
        self.texture.flip_vertical()
###
    def on_touch_down(self, *args, **kwargs):
        super(Camera, self).on_touch_down(*args, **kwargs)
        # Capture an image.
        filename = "/tmp/capture-%d_%f.png" % (self.index, time.time())
        print(filename)
        if self.texture != None: # Camera not connected?
            try: print(self.texture.save(filename, flipped=False))
            except AttributeError: pass # Might be an older version of Kivy
        self.color = [5,5,5,1]
        Clock.schedule_once(self.flash_reset, 0.1)
    def flash_reset(self, *args, **kwargs):
        self.color = [1,1,1,1]

cameras = [MirrorCamera(index=0, resolution=(1280,960), size=(640,480), play=True), MirrorCamera(index=1, resolution=(1280,960), size=(640,480), play=True)] # Capture the highest possible resolution (current v4l + USB2 can't handle more than 720p) but only display low res. This give me highest possible image captures with a standard size widget regardless what cameras are used.

class Main(App):
    def build(self):
        root = FloatLayout()
        root.add_widget(cameras[0])
        cameras[0].pos_hint['center'] = [0.5,0.5]
        return root

Main().run()
