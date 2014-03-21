import kivy
kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout

cameras = [Camera(index=0, resolution=(1280,960), size=(640,480), play=True), Camera(index=1, resolution=(640,480), size=(640,480), play=True)] # May add more than one.

class Main(App):
    def capture(self, btn):
        # Capture an image.
        filename = "/tmp/capture_%d.png" % btn.cam_index
        print(filename)
        return cameras[btn.cam_index].texture.save(filename, flipped=False)
    def flip_on_tex_load(self, cam, *args):
        cam.texture.flip_vertical()
    def build(self):
        root = GridLayout(rows=2) # FIXME/INVESTIGATE: I'd like to be able to add items top-left, bottom-left, top-right, bottom-right. May need to change the order I'm adding things.
        for cam_index in range(0,len(cameras)):
            cam = cameras[cam_index]
            if cam != None:
                if True: ## FIXME: This seems horrible and yucky to me. Why can't I just flip horizontally? And why can't I easily just rotate the camera widget?
                    sctr = Scatter(do_rotation=False, do_scale=False, do_translation_y=False, do_translation_x=False)
                    cam.bind(texture=self.flip_on_tex_load)
                    sctr.rotation = 180
                    sctr.add_widget(cam)
                    root.add_widget(sctr)
                btn = Button(text="Capture")
                btn.cam_index = cam_index
                btn.bind(on_press=self.capture)
                btn.size_hint = [0.1, 0.1]
                root.add_widget(btn)
        return root

Main().run()
