# pcolamakerfaire2023 - Monophonic
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

from menu import Menu, MenuGroup, OscillatorMenuGroup, BarMenuItem, ListMenuItem
from pico_synth_sandbox.audio import get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.oscillator import Oscillator
from pico_synth_sandbox.keyboard.touch import TouchKeyboard

audio = get_audio_driver()
audio.mute()
synth = Synth(audio)
osc1 = Oscillator()
osc2 = Oscillator()
synth.add_voices((osc1, osc2))

keyboard = TouchKeyboard()

menu = Menu((
    MenuGroup((
        BarMenuItem("Level", initial=1.0, update=audio.set_level),
    ), "Snd"),
    MenuGroup((
        ListMenuItem(("High", "Low", "Last"), "Mode", update=keyboard.set_mode),
    ), "Keys"),
    OscillatorMenuGroup(osc1, synth, "Osc1"),
    OscillatorMenuGroup(osc2, synth, "Osc2"),
), "monophonic")

def press(notenum, velocity, keynum=None):
    for voice in synth.voices:
        synth.press(voice, notenum, velocity)
def release(notenum, keynum=None):
    if not keyboard.has_notes():
        synth.release()
keyboard.set_press(press)
keyboard.set_release(release)

# Load last saved state
menu.read()

menu.ready()
audio.unmute()
while True:
    menu.update()
    keyboard.update()
    synth.update()
