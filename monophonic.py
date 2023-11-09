# pcolamakerfaire2023 - Monophonic
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

from menu import Menu, MenuGroup, OscillatorMenuGroup, NumberMenuItem, BarMenuItem, ListMenuItem
from pico_synth_sandbox.audio import get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.oscillator import Oscillator
from pico_synth_sandbox.keyboard.touch import TouchKeyboard
from pico_synth_sandbox.midi import Midi
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
    audio.mute()
    menu.write("monophonic-{:d}".format(int(patch_item.get())))
    audio.unmute()
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

# Midi Implementation
midi = Midi()
midi.set_thru(True)

def control_change(control, value):
    if control == 64: # Sustain
        keyboard.set_sustain(value)
midi.set_control_change(control_change)

def pitch_bend(value):
    for voice in synth.voices:
        voice.set_pitch_bend(value)
midi.set_pitch_bend(pitch_bend)

def note_on(notenum, velocity):
    # Add to keyboard for processing
    keyboard.append(notenum, velocity)
midi.set_note_on(note_on)

def note_off(notenum):
    keyboard.remove(notenum)
midi.set_note_off(note_off)

# Load Patch 0
read_patch()

menu.ready()
audio.unmute()
while True:
    menu.update()
    keyboard.update()
    synth.update()
