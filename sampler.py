# pcolamakerfaire2023 - Sampler
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import gc, os
from pico_synth_sandbox import fftfreq

from menu import Menu, MenuGroup, OscillatorMenuGroup, NumberMenuItem, BarMenuItem, ListMenuItem
from pico_synth_sandbox.keyboard import get_keyboard_driver
from pico_synth_sandbox.audio import Audio, get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.sample import Sample
from pico_synth_sandbox.waveform import Waveform
from pico_synth_sandbox.midi import Midi

# Initialize Objects
audio = get_audio_driver()
audio.mute()
synth = Synth(audio)
synth.add_voices(Sample(loop=False) for i in range(12))
midi = Midi()

# Prepare Sample Files
sample_data = None
sample_rate = Audio.get_sample_rate()
sample_root = 440.0

sample_files = list(filter(lambda x: x[-4:] == ".wav", os.listdir("/samples")))
if not sample_files:
    print("No samples available. Try running \"make samples --always-make\" in the library root directory.")
    exit()

def load_sample(index=0):
    global semitone, sample_data, sample_rate, sample_root

    audio.mute()

    for voice in synth.voices:
        voice.unload()
    del sample_data
    gc.collect()

    sample_data, sample_rate = Waveform.load_from_file("/samples/" + sample_files[index], max_samples=4096)
    sample_root = fftfreq(
        data=sample_data,
        sample_rate=sample_rate
    )
    for voice in synth.voices:
        voice.load(sample_data, sample_rate, sample_root)

    gc.collect()
    audio.unmute()

# Menu System
menu = Menu((
    MenuGroup((
        NumberMenuItem(
            title="Channel",
            step=1,
            maximum=15,
            update=midi.set_channel
        ),
        NumberMenuItem(
            title="Thru",
            step=1,
            maximum=1,
            update=midi.set_thru
        ),
    ), "MIDI"),
    NumberMenuItem(
        title="Thru"
    ),
    BarMenuItem(
        title="Level",
        initial=1.0,
        update=audio.set_level
    ),
    ListMenuItem(
        items=sample_files,
        title="Sample",
        update=load_sample
    ),
    OscillatorMenuGroup(synth.voices, "Osc")
), "sampler")

# Keyboard Setup
keyboard = get_keyboard_driver(root=60)
def press(notenum, velocity, keynum=None):
    if keynum is None:
        keynum = notenum - keyboard.root
    synth.press(keynum % 12, notenum, velocity)
keyboard.set_press(press)
def release(notenum, keynum=None):
    if keynum is None:
        keynum = notenum - keyboard.root
    synth.release(keynum % 12)
keyboard.set_release(release)

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
    keyboard.append(notenum, velocity)
midi.set_note_on(note_on)

def note_off(notenum):
    keyboard.remove(notenum)
midi.set_note_off(note_off)

# Load first sample
load_sample()

menu.ready()
audio.unmute()
while True:
    menu.update()
    keyboard.update()
    synth.update()
    midi.update()
