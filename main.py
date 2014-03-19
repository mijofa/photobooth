import kivy
kivy.require('1.6.0') # This is the version available in the Debian Wheezy apt repo, I would prefer to remain compatible with that.

from kivy.app import App
#from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout

cams = [Camera(index=0, resolution=(640,480), size=(640,480))] # May add more than one

class Main(App):
    def capture(self, *args):
        print(cams[0]._camera.texture)
        print(cams[0]._camera.texture.save('/tmp/capture.png', flipped=False))
    def build(self):
        root = GridLayout()
        cams[0].play = True
        root.add_widget(cams[0])
        btn = Button(text="Capture")
        btn.bind(on_press=self.capture)
        root.add_widget(btn)
        return root

Main().run()
