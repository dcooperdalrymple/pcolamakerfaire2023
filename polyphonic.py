# pcolamakerfaire2023 - Polyphonic
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

from menu import Menu, MenuGroup, OscillatorMenuGroup, NumberMenuItem, BarMenuItem, ListMenuItem
import pico_synth_sandbox.tasks
from pico_synth_sandbox.board import get_board
from pico_synth_sandbox.audio import get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.oscillator import Oscillator
from pico_synth_sandbox.keyboard import get_keyboard_driver
from pico_synth_sandbox.midi import Midi
from pico_synth_sandbox.display import Display

# Initialize Synth and other objects first for reference in menu items
board = get_board()
audio = get_audio_driver(board)
audio.mute()
synth = Synth(audio)
synth.add_voices([Oscillator() for i in range(4)])
keyboard = get_keyboard_driver(board, max_voices=len(synth.voices))
midi = Midi(board)

# Menu and Patch System
class PatchMenuItem(NumberMenuItem):
    def __init__(self, maximum:int=16, update:function=None):
        NumberMenuItem.__init__(self, "Patch", step=1, initial=0, minimum=0, maximum=maximum, loop=True, update=update)
    def set(self, value:float, force:bool=False):
        if force:
            NumberMenuItem.set(self, value)
    def enable(self, display:Display):
        self._group = ""
        NumberMenuItem.enable(self, display)
patch_item = PatchMenuItem()

menu = Menu(board, (
    patch_item,
    MenuGroup((
        NumberMenuItem(
            title="Channel",
            step=1,
            maximum=16,
            update=lambda value : midi.set_channel(int(value))
        ),
        NumberMenuItem(
            title="Thru",
            step=1,
            maximum=1,
            update=lambda value : midi.set_thru(value == 1)
        ),
    ), "MIDI"),
    OscillatorMenuGroup(synth.voices, "Osc"),
), "polyphonic")
default_patch = menu.get()

def read_patch(value=None):
    if value is None:
        value = patch_item.get()
    if not menu.read("polyphonic-{:d}".format(int(value))):
        menu.set(default_patch)
patch_item.set_update(read_patch)

def write_patch():
    audio.mute()
    menu.write("polyphonic-{:d}".format(int(patch_item.get())))
    audio.unmute()
menu.set_write(write_patch)

# Keyboard Setup
def voice_press(index, notenum, velocity, keynum=None):
    synth.press(index, notenum, velocity)
keyboard.set_voice_press(voice_press)

def voice_release(index, notenum, keynum=None):
    synth.release(index)
keyboard.set_voice_release(voice_release)

def key_press(keynum, notenum, velocity):
    midi.send_note_on(notenum, velocity)
keyboard.set_key_press(key_press)

def key_release(keynum, notenum):
    midi.send_note_off(notenum)
keyboard.set_key_release(key_release)

# Midi Implementation
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

def program_change(patch):
    patch_item.set(patch, True)
midi.set_program_change(program_change)

# Load Patch 0
read_patch()

menu.ready()
audio.unmute()

pico_synth_sandbox.tasks.run()
