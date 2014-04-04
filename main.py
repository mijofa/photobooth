#!/usr/bin/python
import kivy
kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout

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

cameras = [MirrorCamera(index=0, resolution=(1280,960), size=(640,480), play=True), MirrorCamera(index=1, resolution=(1280,960), size=(640,480), play=True)] # Capture the highest possible resolution (current v4l + USB2 can't handle more than 720p) but only display low res. This give me highest possible image captures with a standard size widget regardless what cameras are used.

class Main(App):
    def capture(self, btn):
        # Capture an image.
        filename = "/tmp/capture-%d_%f.png" % (btn.cam_index, time.time())
        print(filename)
        return cameras[btn.cam_index].texture.save(filename, flipped=False)
    def build(self):
        root = GridLayout(rows=1) # FIXME/INVESTIGATE: I'd like to be able to add items top-left, bottom-left, top-right, bottom-right. May need to change the order I'm adding things.
        root.spacing = 10
        for cam_index in range(0,len(cameras)):
            cam = cameras[cam_index]
            if cam != None:
                col = GridLayout(rows=2) # I want to create a column at a time, this seems easiest.
                col.add_widget(cam)
                btn = Button(text="Capture")
                btn.cam_index = cam_index
                btn.bind(on_press=self.capture)
                btn.size_hint = [0.1, 0.1]
                col.add_widget(btn)
                root.add_widget(col)
        return root

Main().run()
