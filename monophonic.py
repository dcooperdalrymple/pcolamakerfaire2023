# pcolamakerfaire2023 - Monophonic
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

from menu import Menu, MenuGroup, OscillatorMenuGroup, NumberMenuItem, BarMenuItem, ListMenuItem
from pico_synth_sandbox.audio import get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.oscillator import Oscillator
from pico_synth_sandbox.keyboard.touch import TouchKeyboard
from pico_synth_sandbox.display import Display

# Initialize Synth and other objects first for reference in menu items
audio = get_audio_driver()
audio.mute()
synth = Synth(audio)
osc1 = Oscillator()
osc2 = Oscillator()
synth.add_voices((osc1, osc2))
keyboard = TouchKeyboard()

# Menu and Patch System
class PatchMenuItem(NumberMenuItem):
    def __init__(self, maximum:int=16, update:function=None):
        NumberMenuItem.__init__(self, "Patch", step=1, initial=0, minimum=0, maximum=maximum, loop=True, update=update)
    def set(self, value:float):
        pass
    def enable(self, display:Display):
        self._group = ""
        NumberMenuItem.enable(self, display)
patch_item = PatchMenuItem()

menu = Menu((
    patch_item,
    MenuGroup((
        BarMenuItem("Level", initial=1.0, update=audio.set_level),
    ), "Snd"),
    MenuGroup((
        ListMenuItem(("High", "Low", "Last"), "Mode", update=keyboard.set_mode),
    ), "Keys"),
    OscillatorMenuGroup(osc1, synth, "Osc1"),
    OscillatorMenuGroup(osc2, synth, "Osc2"),
), "monophonic")
default_patch = menu.get()

def read_patch(value=None):
    if value is None:
        value = patch_item.get()
    if not menu.read("monophonic-{:d}".format(int(value))):
        menu.set(default_patch)
patch_item.set_update(read_patch)

def write_patch():
    menu.write("monophonic-{:d}".format(int(patch_item.get())))
menu.set_write(write_patch)

# Keyboard Setup
def press(notenum, velocity, keynum=None):
    for voice in synth.voices:
        synth.press(voice, notenum, velocity)
keyboard.set_press(press)

def release(notenum, keynum=None):
    if not keyboard.has_notes():
        synth.release()
keyboard.set_release(release)

# Load Patch 0
read_patch()

menu.ready()
audio.unmute()
while True:
    menu.update()
    keyboard.update()
    synth.update()
