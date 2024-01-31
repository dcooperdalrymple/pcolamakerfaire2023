# pcolamakerfaire2023 - Sampler
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import gc, os
from pico_synth_sandbox import fftfreq

from menu import Menu, MenuGroup, OscillatorMenuGroup, NumberMenuItem, BarMenuItem, ListMenuItem
import pico_synth_sandbox.tasks
from pico_synth_sandbox.board import get_board
from pico_synth_sandbox.keyboard import get_keyboard_driver
from pico_synth_sandbox.audio import Audio, get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.sample import Sample
import pico_synth_sandbox.waveform as waveform
from pico_synth_sandbox.midi import Midi

# Initialize Objects
board = get_board()
audio = get_audio_driver(board)
audio.mute()
synth = Synth(audio)
synth.add_voices(Sample(loop=False) for i in range(4))
midi = Midi(board)

# Prepare Sample Files
sample_data = None
sample_rate = audio.get_sample_rate()
sample_root = 440.0

sample_files = list(filter(lambda x: x[-4:] == ".wav", os.listdir("/samples")))
if not sample_files:
    print("No samples available. Try running \"make samples --always-make\" in the library root directory.")
    exit()

def load_sample(index=0):
    global semitone, sample_data, sample_rate, sample_root

    audio.mute()
    pico_synth_sandbox.tasks.pause()

    for voice in synth.voices:
        voice.unload()
    del sample_data
    gc.collect()

    sample_data, sample_rate = waveform.load_from_file("/samples/" + sample_files[index], max_samples=4096)
    sample_root = fftfreq(
        data=sample_data,
        sample_rate=sample_rate
    )
    for voice in synth.voices:
        voice.load(sample_data, sample_rate, sample_root)

    gc.collect()
    pico_synth_sandbox.tasks.resume()
    audio.unmute()

# Menu System
menu = Menu(board, (
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
keyboard = get_keyboard_driver(board, root=60, max_voices=len(synth.voices))
def press(voice, notenum, velocity, keynum=None):
    synth.press(voice, notenum, velocity)
    midi.send_note_on(notenum, velocity)
keyboard.set_voice_press(press)

def release(voice, notenum, keynum=None):
    synth.release(voice)
    midi.send_note_off(notenum)
keyboard.set_voice_release(release)

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

def program_change(patch):
    if patch < len(sample_files):
        load_sample(patch)
midi.set_program_change(program_change)

# Load first sample
load_sample()

menu.ready()
audio.unmute()

pico_synth_sandbox.tasks.run()
