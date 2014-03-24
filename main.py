import kivy
kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout

import time

cameras = [Camera(index=0, resolution=(1280,960), size=(640,480), play=True), Camera(index=1, resolution=(1280,960), size=(640,480), play=True)] # Capture the highest possible resolution (current v4l + USB2 can't handle more than 720p) but only display low res. This give me highest possible image captures with a standard size widget regardless what cameras are used.

class Main(App):
    def capture(self, btn):
        # Capture an image.
        filename = "/tmp/capture-%d_%f.png" % (btn.cam_index, time.time())
        print(filename)
        return cameras[btn.cam_index].texture.save(filename, flipped=False)
    def flip_on_tex_load(self, cam, *args):
        cam.texture.flip_vertical()
    def build(self):
        root = GridLayout(rows=1) # FIXME/INVESTIGATE: I'd like to be able to add items top-left, bottom-left, top-right, bottom-right. May need to change the order I'm adding things.
        root.spacing = 10
        for cam_index in range(0,len(cameras)):
            cam = cameras[cam_index]
            if cam != None:
                col = GridLayout(rows=2) # I want to create a column at a time, this seems easiest.
                if True: ## FIXME: This seems horrible and yucky to me. Why can't I just flip horizontally? And why can't I easily just rotate the camera widget?
                    # Seems the only good way to rotate a widget without using Scatter is to use the .kv language. No big deal I can do that.
                    # Oh wait, no I can't. Because Kivy 1.6.0 doesn't support the 'origin' option to rotate so it will always rotate around the bottom-left corner. *grumble grumble*
                    sctr = Scatter(do_rotation=False, do_scale=False, do_translation_y=False, do_translation_x=False)
                    cam.bind(texture=self.flip_on_tex_load)
                    sctr.rotation = 180
                    sctr.add_widget(cam)
                    col.add_widget(sctr)
                btn = Button(text="Capture")
                btn.cam_index = cam_index
                btn.bind(on_press=self.capture)
                btn.size_hint = [0.1, 0.1]
                col.add_widget(btn)
                root.add_widget(col)
        return root

Main().run()
