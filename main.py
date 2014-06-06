#!/usr/bin/python
import os.path


import kivy
#kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?
### Aww, Kivy 1.6.0 can't save camera textures either. :(
# I give up 1.6.0 will not work with this at all

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

COUNTDOWN_LENGTH = 3

#VIDEO_DEVICE = "/dev/v4l/by-id/usb-Vimicro_Corp._PC_Camera-video-index0" # Crappy camera
#VIDEO_DEVICE = "/dev/v4l/by-id/usb-046d_0825_6E2E6170-video-index0" # Good camera
VIDEO_DEVICE = "/dev/video0"
SAVE_PATH = "/mnt/tmp"

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
    # This is a bad hack, but I CBFed doing it properly.
    # I need to be able to specify the device path rather than just the /dev/video index
    def init_camera(self):
        orig_video_src = self._video_src
        try: self._video_src = 'v4l2src device=%s' % VIDEO_DEVICE
        except: self._video_src = orig_video_src
        super(CoreCamera, self).init_camera()
kivy.core.camera.Camera = CoreCamera
from kivy.uix.camera import Camera

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
    repeats = 0
    repeat_num = 0
    repeat_interval = 0.2
    def __init__(self, *args, **kwargs):
        self.register_event_type('on_capture_end')
        super(MirrorCamera, self).__init__(*args, **kwargs)
        self._camera.bind(on_texture=lambda args: self.texture.flip_vertical()) # I use lambda here because self.texture.flip_vertical doesn't exist yet.
    def on_capture_end(self, *args, **kwargs):
        # This triggers when all repeated image captures are finished.
        # I use this to reset the info text when finished.
        pass
    def capture_image(self, dt = None, repeats = 0, interval = 0.2):
        # This function just sets the colour of the widget to lots of white to simulate a flash then tells the Clock to actually capture an image after rendering the next frame.
        # I split this into 2 functions because if capture th image before rendering the next frame the "flash" never gets rendered
        self.repeats = repeats
        self.repeat_interval = interval
        self._pre_capture()
    def _pre_capture(self, dt = None):
        # The entire purpose of this function is to simulate a flash by setting the colour to all white.
        ## NOTE: Stop trying to put this into the _actual_capture function!!! It can't work.
        ## Setting the screen to white, and setting it back to normal needs to be in different clock cycles otherwise Kivy doesn't render the screen in between and you end up with no flash at all.
        ## So this function tells Kivy to call the _actual_capture function on the next clock cycle.
        self.color = [5,5,5,1]
        Clock.schedule_once(self._actual_capture, 0)
    def _actual_capture(self, dt = None):
        # Capture an image, then reset the simulated flash
        filename = "capture-%d_%f.jpg" % (self.index, time.time())
        if self.texture != None: # Camera not connected?
            try: self.texture.save(os.path.join(SAVE_PATH, filename), flipped=False)
            except AttributeError: pass # Might be an older version of Kivy
        self.color = [1,1,1,1]
        self.repeat_num += 1
        if self.repeat_num >= self.repeats or self.repeats == 0:
            self.repeat_num = 0
#            Clock.schedule_once(lambda args: self.dispatch('on_capture_end'), self.repeat_interval)
            return False
        elif self.repeats >  0:
            Clock.schedule_once(self._pre_capture, self.repeat_interval)
            return True

class Main(App):
    def start_countdown(self, *args):
        self.stop_countdown() # Stop any countdown already in progress.
        self._countdown(0) # Run it now otherwise it will take 1 second before the countdown starts.
        Clock.schedule_interval(self._countdown, 1) # Start a new countdown.
        return True
    def stop_countdown(self):
        self.countdown_number.text = ''
        Clock.unschedule(self._countdown)
        self.capture_end()
    def _countdown(self, dt = None):
        if self.countdown_number.text == '': # Countdown hasn't been run yet.
            self.info.text = "Get ready..."
            self.countdown_number.text = str(COUNTDOWN_LENGTH)
            return True # Run this again on the next loop
        elif self.countdown_number.text == 'Smile!': # Finished the countdown.
            self.countdown_number.text = ''
            self.cam.capture_image(repeats=3)
            return False # Stop running this
        new_num = int(self.countdown_number.text)-1
        if new_num == 0:
            self.countdown_number.text = 'Smile!'
            self.info.text = ''
        else:
            self.countdown_number.text = str(new_num)
        return True # Run this again on the next loop
    def capture_end(self, *args):
        self.info.text = "Press button to start countdown."
    def build(self):
        self.root = FloatLayout()

        self.cam = MirrorCamera(index=0, resolution=(1280,960), play=True, stopped=False)
        self.cam.pos_hint['center'] = [0.5,0.5]
        self.cam.size_hint = [1,1]
        self.cam.bind(on_capture_end=self.capture_end)
        self.root.add_widget(self.cam)
        self.cam.bind(on_touch_down=self.start_countdown)

#        picture_btn = Button(size_hint=[0.33, 0.1], on_press=self.start_countdown,
#                pos_hint={'top': 0.1, 'center_x': 0.5},
#                text="Take photo",
#                background_color=[1,0,0,1],
#            )
#        self.root.add_widget(picture_btn)

        self.info = Label(color=[1,0,0,1], font_size=32, pos_hint={'center': [0.5,0.95]})
        self.root.add_widget(self.info)
        self.capture_end()

        self.countdown_number = Label(text='', color=[0,1,0,0.5], font_size=256, pos_hint={'center': [0.5,0.5]})
        self.root.add_widget(self.countdown_number)


        ### Get keyboard keypress
        kbd = Window.request_keyboard(None, self.cam) #, 'text')
        kbd.bind(
                on_key_down=self.start_countdown,
#                on_key_up= ,
        )


        return self.root

Main().run()
