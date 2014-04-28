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
from kivy.graphics import Rectangle
from kivy.graphics import Color
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout

VIDEO_DEVICE = "/dev/v4l/by-id/usb-Vimicro_Corp._PC_Camera-video-index0"
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
        self._camera.bind(on_texture=lambda args: self.texture.flip_vertical()) # I use lambda here because self.texture.flip_vertical doesn't exist yet. # This line replaces the commented out _camera_loaded function above.
    def on_capture_end(self, *args, **kwargs):
        # This triggers when all repeated image captures are finished.
        # I use this to reset the info text when finished.
        pass
    def capture_image(self, dt = None, repeats = None, interval = None):
        # This function just sets the colour of the widget to lots of white to simulate a flash then tells the Clock to actually capture an image after rendering the next frame.
        # I split this into 2 functions because if capture th image before rendering the next frame the "flash" never gets rendered
        self.color = [5,5,5,1]
        if repeats != None:
            self.repeats = repeats
        if interval != None:
            self.repeat_interval = interval
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
            self.repeat_interval = 0.2
            self.repeat_num = 0
            self.repeats = 0
#            Clock.schedule_once(lambda args: self.dispatch('on_capture_end'), self.repeat_interval)
            return False
        elif self.repeats >  0:
            Clock.schedule_once(self.capture_image, self.repeat_interval)
            return True
    def start_vid_capture(self, length, mute=True):
        raise NotImplemented('Video capture has been disabled for now.')
        filename = "capture-%d_%f.ogv" % (self.index, time.time())
        self._camera.capture_video_start(os.path.join(SAVE_PATH, filename), mute)
#        Clock.schedule_once(self._finish_capture_video, length)
    def stop_vid_capture(self, dt = None):
        self._camera.capture_video_stop()
#        self.dispatch('on_capture_end')
        pass


class Main(App):
    def countdown(self, btn = None):
        if btn != None and type(btn) != float and type(btn) != int:
            Clock.unschedule(self.countdown)
            self.countdown_info = btn.countdown_info
        if self.countdown_number.text == '': # Countdown hasn't been run yet.
            Clock.schedule_interval(self.countdown, 1)
            self.info.text = "Get ready..."
            self.countdown_number.text = '3' # FINDME: Countdown length.
            return True
        elif self.countdown_number.text == '1':
            self.info.text = self.countdown_info['final_text']
        elif self.countdown_number.text == '0': # Finished the countdown.
            self.info.text = ''
            self.countdown_number.text = ''
            if self.countdown_info['capture_type'] == 'picture':
                self.cam.capture_image(repeats=3)
            elif self.countdown_info['capture_type'] == 'video':
#                self.recording_indicator.color = [0,1,0,1]
                self.recording_indicator.opacity = 1
                self.recording_indicator.text = '10'
                self.vid_timer(self.recording_indicator)
                self.cam.start_vid_capture(length=10, mute=True)
            elif self.countdown_info['capture_type'] == 'audio_video':
                self.audio_recording_indicator.opacity = 1
                self.audio_recording_indicator.text = '10'
                self.vid_timer(self.audio_recording_indicator)
                self.cam.start_vid_capture(length=10, mute=False)
            return False
        self.countdown_number.text = str(int(self.countdown_number.text)-1)
    def vid_timer(self, indicator): # indicator will actually be dt most of the time, but I ignore dt anyway.
        if type(indicator) != int and type(indicator) != float:
            self.timer = indicator
            Clock.schedule_once(self.vid_timer, 1)
            return
        if self.timer.text != '0':
            self.timer.text = str(int(self.timer.text)-1)
            Clock.schedule_once(self.vid_timer, 1)
        else:
            self.timer.text = ''
            self.cam.stop_vid_capture()
    def display_reset(self, *args):
        self.info.text = "Touch screen to take photo"
        self.recording_indicator.opacity = 0
        self.audio_recording_indicator.opacity = 0
    def build(self):
        self.root = FloatLayout()

        self.cam = MirrorCamera(index=0, resolution=(1280,960), size=(640,480), play=True, video_src='sdkjnb')
        self.cam.pos_hint['center'] = [0.5,0.55]
        self.cam.size_hint = [1,0.9]
        self.cam.bind(on_capture_end=self.display_reset) # I believe using setattr is evil, but it seemed easier than any alternative I could think of.
        self.root.add_widget(self.cam)

        self.recording_indicator = Label(pos_hint={'top': 0.95, 'right': 0.95}, color=[1,1,1,1], size_hint=(0.05,0.05))
        with self.recording_indicator.canvas.before:
            self.recording_indicator.background_image = Rectangle(source='rec_noaud.png', size=self.recording_indicator.size, pos=self.recording_indicator.pos)
        self.recording_indicator.opacity = 0

        self.audio_recording_indicator = Label(pos_hint={'top': 0.95, 'right': 0.95}, color=[1,1,1,1], size_hint=(0.05,0.05))
        with self.audio_recording_indicator.canvas.before:
            self.audio_recording_indicator.background_image = Rectangle(source='rec_aud.png', size=self.audio_recording_indicator.size, pos=self.audio_recording_indicator.pos)
        self.audio_recording_indicator.opacity = 0

        def update_background(instance, value):
            instance.background_image.size = instance.size[0], instance.size[0] # Using size_hint above doesn't garauntee a square, but I want the circle size to be locked to being a square.
            instance.background_image.pos = instance.pos
        self.recording_indicator.bind(size=update_background, pos=update_background)
        self.audio_recording_indicator.bind(size=update_background, pos=update_background)
        self.root.add_widget(self.recording_indicator)
        self.root.add_widget(self.audio_recording_indicator)

        picture_btn = Button(size_hint=[0.33, 0.1], on_press=self.countdown,
                pos_hint={'top': 0.1, 'left': '0'},
                text="Picture",
                background_color=[0,0,1,1],
            )
        picture_btn.countdown_info = {
                'final_text': "Smile!",
                'capture_type': 'picture'
            }
        self.root.add_widget(picture_btn)

        video_btn = Button(size_hint=[0.33, 0.1], on_press=self.countdown,
                pos_hint={'top': 0.1, 'center_x': 0.5},
                text='10s Video',
                background_color=[0,1,0,1],
            )
        video_btn.countdown_info = {
                'final_text': "Action!",
                'capture_type': 'video'
            }
        self.root.add_widget(video_btn)

        audio_video_btn = Button(size_hint=[0.33, 0.1], on_press=self.countdown,
                pos_hint={'top': 0.1, 'right': 1},
                text='10s Video with audio',
                background_color=[1,0,0,1],
            )
        audio_video_btn.countdown_info = {
                'final_text': "Action!",
                'capture_type': 'audio_video'
            }

        self.root.add_widget(audio_video_btn)

        self.info = Label(text="Touch screen to take photo", color=[1,0,0,1], font_size=32, pos_hint={'center': [0.5,0.95]})
        self.root.add_widget(self.info)

        self.countdown_number = Label(text='', color=[0,1,0,0.5], font_size=256, pos_hint={'center': [0.5,0.5]})
        self.root.add_widget(self.countdown_number)

        return self.root

Main().run()
