#!/usr/bin/python
import kivy
kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?
### Aww, Kivy 1.6.0 can't save camera textures either. :(

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
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
    def _camera_loaded(self, *largs): # I really don't like overriding this function, but it works so I'm not touching it anymore
        self.texture = self._camera.texture
        self.texture_size = list(self.texture.size)
        self.texture.flip_vertical()
###
    def capture_image(self, *args, **kwargs):
        # Capture an image.
        filename = "/tmp/capture-%d_%f.png" % (self.index, time.time())
        if self.texture != None: # Camera not connected?
            try: print(self.texture.save(filename, flipped=False))
            except AttributeError: pass # Might be an older version of Kivy
        self.color = [5,5,5,1]
        Clock.schedule_once(self.flash_reset, 0.05)
    def flash_reset(self, *args, **kwargs):
        self.color = [1,1,1,1]

cameras = [MirrorCamera(index=0, resolution=(1280,960), size=(640,480), play=True), MirrorCamera(index=1, resolution=(1280,960), size=(640,480), play=True)] # Capture the highest possible resolution (current v4l + USB2 can't handle more than 720p) but only display low res. This give me highest possible image captures with a standard size widget regardless what cameras are used.

class Main(App):
    def countdown(self, *args, **kwargs):
        if self.countdown_number.text == '': # Countdown hasn't been run yet.
            Clock.schedule_interval(self.countdown, 1)
            self.info.text = "Get ready..."
            self.countdown_number.text = '3' # FINDME: Countdown length.
            return
        elif self.countdown_number.text == '1':
            self.info.text = "Smile!"
        elif self.countdown_number.text == '0': # Finished the countdown.
            self.info.text = ''
            Clock.schedule_once(cameras[0].capture_image, 0.0) # I could have done these 3 as a schedule_interval and have it return False after 3 runs the same way this function does... But that was too hard.
            Clock.schedule_once(cameras[0].capture_image, 0.2)
            Clock.schedule_once(cameras[0].capture_image, 0.4)
            Clock.schedule_once(lambda args: setattr(self.info, 'text', "Touch screen to take photo"), 0.5) # I believe using setattr is evil, but it seemed easier than any alternative I could think of.
            self.info.text = ''
            self.countdown_number.text = ''
            return False # This removes the function from the schedule_interval
        self.countdown_number.text = str(int(self.countdown_number.text)-1)
    def build(self):
        self.root = FloatLayout()
        self.root.add_widget(cameras[0])
        cameras[0].pos_hint['center'] = [0.5,0.5]
        cameras[0].bind(on_touch_down=self.countdown)
        self.info = Label(text="Touch screen to take photo", color=[1,0,0,1], font_size=32, pos_hint={'center': [0.5,0.9]})
        self.root.add_widget(self.info)
        self.countdown_number = Label(text='', color=[0,1,0,0.5], font_size=256, pos_hint={'center': [0.5,0.5]})
        self.root.add_widget(self.countdown_number)
        return self.root

Main().run()
