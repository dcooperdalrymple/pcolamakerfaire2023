# pico_synth_sandbox - Drum Sequencer Example
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import pico_synth_sandbox.tasks
from pico_synth_sandbox.board import get_board
from pico_synth_sandbox.display import Display
from pico_synth_sandbox.encoder import Encoder
from pico_synth_sandbox.keyboard import get_keyboard_driver
from pico_synth_sandbox.sequencer import Sequencer
from pico_synth_sandbox.audio import get_audio_driver
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice.drum import Kick, Snare, ClosedHat, OpenHat
from pico_synth_sandbox.midi import Midi

board = get_board()

display = Display(board)
display.write("PicoSynthSandbox", (0,0))
display.write("Loading...", (0,1))
display.set_cursor_blink(False)

# Local parameters
voice=0
bpm=120
alt_enc=False
alt_key=False

audio = get_audio_driver(board)
synth = Synth(audio)
synth.add_voices([
    Kick(),
    Snare(),
    ClosedHat(),
    OpenHat()
])
midi = Midi(board)

sequencer = Sequencer(
    tracks=len(synth.voices),
    bpm=120
)
def seq_step(position):
    display.show_cursor(position, 1)
def seq_press(notenum, velocity):
    synth.press((notenum - 1) % len(synth.voices))
def seq_release(notenum):
    if (notenum - 1) % len(synth.voices) == 2: # Closed Hat
        synth.release(3, True) # Force release Open Hat
    synth.release((notenum - 1) % len(synth.voices))
sequencer.set_step(seq_step)
sequencer.set_press(seq_press)
sequencer.set_release(seq_release)

def update_display():
    display.write(synth.voices[voice].__qualname__, (0, 0), 11)
    display.write(">" if alt_enc else "<", (11,0), 1)
    display.write(("^" if alt_key else "-") if len(keyboard.keys) < 16 else " ", (12,0), 1)
    display.write(str(bpm), (13,0), 3, True)
    line = ""
    for i in range(sequencer.get_length()):
        line += "*" if sequencer.has_note(i, voice) else "_"
    display.write(line, (0,1))

keyboard = get_keyboard_driver(board, max_voices=0)
def key_press(keynum, notenum, velocity):
    global voice

    if len(keyboard.keys) < 16:
        global alt_key
        if keynum == 11:
            alt_key = not alt_key
            display.write("^" if alt_key else "-", (12,0), 1)
            return
        elif keynum < 8:
            position = keynum + (8 if alt_key else 0)
    else:
        position = keynum

    position = position % sequencer.get_length()
    if not sequencer.has_note(
        position=position,
        track=voice
    ):
        sequencer.set_note(
            position=position,
            notenum=voice+1,
            velocity=1.0,
            track=voice
        )
        display.write("*", (position,1), 1)
    else:
        sequencer.remove_note(
            position=position,
            track=voice
        )
        display.write("_", (position,1), 1)
keyboard.set_key_press(key_press)

def update_bpm():
    sequencer.set_bpm(bpm)
    display.write(str(bpm), (13,0), 3, True)
def update_selected():
    global alt_enc
    display.write(">" if alt_enc else "<", (11,0), 1)
def increment_voice():
    global voice, alt_enc
    if alt_enc:
        alt_enc = False
        update_selected()
    voice = (voice + 1) % sequencer.get_tracks()
    update_display()
def decrement_voice():
    global voice, alt_enc
    if alt_enc:
        alt_enc = False
        update_selected()
    voice = (voice - 1) % sequencer.get_tracks()
    update_display()
def increment_bpm():
    global bpm, alt_enc
    if not alt_enc:
        alt_enc = True
        update_selected()
    if bpm < 200:
        bpm += 1
        update_bpm()
def decrement_bpm():
    global bpm, alt_enc
    if not alt_enc:
        alt_enc = True
        update_selected()
    if bpm > 50:
        bpm -= 1
        update_bpm()
def encoder_increment():
    if not alt_enc:
        increment_voice()
    else:
        increment_bpm()
def encoder_decrement():
    if not alt_enc:
        decrement_voice()
    else:
        decrement_bpm()
def encoder_toggle():
    global alt_enc
    alt_enc = not alt_enc
    update_selected()
def toggle_sequencer():
    sequencer.toggle()
def clear_track():
    for i in range(sequencer.get_length()):
        sequencer.remove_note(position=i, track=voice)
    update_display()

update_display()

if board.num_encoders() == 1:
    encoder = Encoder(board)
    encoder.set_increment(encoder_increment)
    encoder.set_decrement(encoder_decrement)
    encoder.set_click(encoder_toggle)
    encoder.set_double_click(toggle_sequencer)
elif board.num_encoders() > 1:
    encoders = (Encoder(board, 0), Encoder(board, 1))
    encoders[0].set_increment(increment_voice)
    encoders[0].set_decrement(decrement_voice)
    encoders[0].set_long_press(clear_track)
    encoders[1].set_increment(increment_bpm)
    encoders[1].set_decrement(decrement_bpm)
    encoders[1].set_click(toggle_sequencer)
    # TODO: encoders[1].set_long_press(save_sequence)

pico_synth_sandbox.tasks.run()
