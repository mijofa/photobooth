#!/usr/bin/python
COUNTDOWN_LENGTH = 3

VIDEO_DEVICE = "/dev/video0"
SAVE_PATH = "/srv/share/Photos"

import threading
import sys, getopt
import os
options, arguments = getopt.gnu_getopt(sys.argv[1:], 'd:')
for o, a in options:
    if o == '-d':
        VIDEO_DEVICE = a
for a in arguments:
    if os.path.isdir(a):
        SAVE_PATH = os.path.normpath(a)

import time
import string # Hopefully this module will *never* get used, but it's her as a fallback in case we run out of random adjective+animal combinations.
import random
with open('adjectives-list', 'r') as f:
    adjectives = [line.strip() for line in f.readlines()]
with open('animals-list', 'r') as f:
    animals = [line.strip() for line in f.readlines()]
def gen_random_string(used = [], attempt = 0):
    # I know the recursive functions are probably a bad thing, but I figured Python's recursion limit would make a good fallback in case mine fail.
    adjective = random.choice(adjectives)
    animal = random.choice(animals)
    if attempt >= 602:
        raise Exception('Tried %d times and could not find a unique random string.')
    if attempt >= 600:
        random_string = time.time()
    elif attempt >= 500:
        random_string = ''.join(random.choice(string.lowercase+string.digits) for _ in range(8))
    elif attempt >= 200:
        adjective += ' '
        adjective += random.choice(adjectives)
        random_string = adjective+' '+animal
    else:
        random_string = adjective+' '+animal
    if random_string in used:
        random_string = gen_random_string(used=used, attempt=attempt+1)
    return random_string

import kivy
#kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.
### So with Kivy 1.6.0 on my netbook the scatter().rotation works, but the Camera().texture.flip_vertical() does no. Is this the Kivy version or the camera?
### Aww, Kivy 1.6.0 can't save camera textures either. :(
# I give up, 1.6.0 will not work with this at all
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Ellipse, Color, Callback

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
    repeat_interval = 0
    def __init__(self, *args, **kwargs):
        self.register_event_type('on_capture_start')
        self.register_event_type('on_capture_timer')
        self.register_event_type('on_capture_end')
        super(MirrorCamera, self).__init__(*args, **kwargs)
        self._camera.bind(on_texture=lambda args: self.texture.flip_vertical()) # I use lambda here because self.texture.flip_vertical doesn't exist yet.
    def on_capture_start(self, *args, **kwargs):
        pass
    def on_capture_end(self, *args, **kwargs):
        # This triggers when all repeated image captures are finished.
        # I use this to reset the info text when finished.
        pass
    def on_capture_timer(self, *args, **kwargs):
        pass
    def capture_image(self, dt = None, repeats = 0):
        # This function just sets the colour of the widget to lots of white to simulate a flash then tells the Clock to actually capture an image after rendering the next frame.
        # I split this into 2 functions because if capture th image before rendering the next frame the "flash" never gets rendered
        self.repeats = repeats
        self.repeat_interval = 1

        self.rand_id = gen_random_string(used=os.listdir(SAVE_PATH))
        self.save_dir = os.path.join(SAVE_PATH, self.rand_id)
        os.mkdir(self.save_dir)

        self._pre_capture()
    def _pre_capture(self, dt = None):
        # The entire purpose of this function is to simulate a flash by setting the colour to all white.
        ## NOTE: Stop trying to put this into the _actual_capture function!!! It can't work.
        ## Setting the screen to white, and setting it back to normal needs to be in different clock cycles otherwise Kivy doesn't render the screen in between and you end up with no flash at all.
        ## So this function tells Kivy to call the _actual_capture function on the next clock cycle.
        self.dispatch('on_capture_start')
        self.color = [5,5,5,1]
        Clock.schedule_once(self._actual_capture, 0)
    def _actual_capture(self, dt = None):
        # Capture an image, then reset the simulated flash
        threading.Thread(target=lambda:self.texture.save(os.path.join(self.save_dir, "%d.jpg" % self.repeat_num), flipped=False)).start()
        self.color = [1,1,1,1]
        self.repeat_num += 1
        if self.repeat_num >= self.repeats or self.repeats == 0:
            self.repeat_num = 0
            Clock.schedule_once(lambda args: self.dispatch('on_capture_end'), 0.3)
        elif self.repeats >  0:
            self.dispatch('on_capture_timer')
            Clock.schedule_once(self._pre_capture, self.repeat_interval)
        return

class Main(App):
    time = 0.0
    def start_countdown(self, *args):
        self.file_info.text = ''
        Clock.unschedule(self.clear_file_label)
        self.stop_countdown() # Stop any countdown already in progress.
        self._countdown() # Run it now otherwise it will take 1 second before the countdown starts.
        Clock.schedule_interval(self._countdown, 0.01) # Start a new countdown.
        return True
    def stop_countdown(self, *args):
        Clock.unschedule(self._countdown)
        self.countdown_number.text = ''
        Clock.unschedule(self.single_second_countdown)
        self.countdown_number.angle_start = 360
        self.countdown_number.bg_col = (1,0,0,0.5)
    def single_second_countdown(self, dt=0):
        if type(dt) != int and type(dt) != float:
            self.time = 0.0
            Clock.schedule_interval(self.single_second_countdown, 0.01)
            self.countdown_number.angle_start = 0
            self.countdown_number.bg_col = (0.25,1,0.25,0.5)
            self.countdown_number.cb.ask_update()
            return
        self.time += dt
        self.countdown_number.angle_start = self.time*360
        if self.countdown_number.angle_start > 360:
            self.countdown_number.angle_start = 360
        self.countdown_number.cb.ask_update()
        if self.time >= 1:
            return False
        else:
            return True
    def _countdown(self, dt = None):
        if not dt == None:
            self.time += dt
            if self.time == 0:
                self.countdown_number.angle_start = 0
            elif self.time >= 1:
                self.countdown_number.angle_start = 360
            else:
                self.countdown_number.angle_start = self.time*360
            self.countdown_number.cb.ask_update()
        if self.time >= 1 or dt == None:
            self.time = 0
            if self.countdown_number.text == '3':
                self.countdown_number.bg_col = (1,0.5,0,0.5)
            if self.countdown_number.text == '2':
                self.countdown_number.bg_col = (1,1,0,0.5)
            elif self.countdown_number.text == '' and self.info.text == 'Smile!': # Finished the countdown.
                self.countdown_number.angle_start = 360
                self.countdown_number.bg_col = (1,0,0,0.5)
                self.countdown_number.text = ''
                self.cam.capture_image(repeats=3)
                return False # Stop running this
            elif self.countdown_number.text == '': # Countdown hasn't been run yet.
                self.info.text = "Get ready..."
                self.countdown_number.text = str(COUNTDOWN_LENGTH)
                return True # Run this again on the next loop
            new_num = int(self.countdown_number.text)-1
            if new_num == 0:
                self.info.text = 'Smile!'
                self.countdown_number.text = ''
                self.countdown_number.bg_col = (0,1,0,0.5)
            else:
                self.countdown_number.text = str(new_num)
        return True # Run this again on the next loop
    def capture_end(self, cam = None, *args):
        self.info.text = "Press button to start countdown."
        self.countdown_number.angle_start = 360
        self.countdown_number.bg_col = (1,0,0,0.5)
        if cam != None:
            self.file_info.text = "Your photos have been saved as '%s'" % cam.rand_id
            Clock.schedule_once(self.clear_file_label, 10)
    def clear_file_label(self, *args):
        self.file_info.text = ''
    def build(self):
        self.root = FloatLayout()

        self.cam = MirrorCamera(index=0, resolution=(1280,960), play=True, stopped=False, allow_stretch=True)
        self.cam.pos_hint['center'] = [0.5,0.5]
        self.cam.size_hint = [1,1]
        self.cam.bind(on_capture_start=self.stop_countdown)
        self.cam.bind(on_capture_end=self.capture_end)
        self.cam.bind(on_capture_timer=self.single_second_countdown)
        self.root.add_widget(self.cam)
        self.cam.bind(on_touch_down=self.start_countdown)

        self.info = Label(color=[1,0,0,1], font_size=96, pos_hint={'center': [0.5,0.9]})
        self.root.add_widget(self.info)

        self.file_info = Label(color=[0,1,0,1], font_size=64, pos_hint={'center': [0.5,0.05]})
        self.root.add_widget(self.file_info)

        self.countdown_number = Label(text='', color=[0,1,0,0.5], font_size=256, pos_hint={'center': [0.5,0.5]},size_hint=[0.25,0.25])
        self.root.add_widget(self.countdown_number)
        with self.countdown_number.canvas:
            self.countdown_number.cb = Callback(self.redraw_timer)
        self.countdown_number.bind(size=lambda a, b: self.countdown_number.cb.ask_update(), pos=lambda a, b: self.countdown_number.cb.ask_update())

        ### Get keyboard keypress
        kbd = Window.request_keyboard(None, self.cam) #, 'text')
        kbd.bind(
                on_key_down=self.start_countdown,
#                on_key_up= ,
        )

        self.capture_end() # This sets some of the display correctly
        return self.root
    def redraw_timer(self, cb):
        pos = (
                (self.root.size[0]-256)/2,
                (self.root.size[1]-256)/2,
                )
        instance = self.countdown_number
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*instance.bg_col)
            Ellipse(
                    angle_end=360,angle_start=instance.angle_start,
                    pos=pos,size=(256,256),
            )

Main().run()
