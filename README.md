# Pensacola Maker Faire 2023: pico_synth_sandbox Demonstrations
A collection of [pico_synth_sandbox](https://github.com/dcooperdalrymple/pico_synth_sandbox) demonstrations for the 2023 Pensacola Maker Faire.

## General Features
Each program features the following functionality at minimum.
* Recursive menu system with extensive parameter control
* JSON patch reading & writing with 16 available presets _(can be expanded to allow more)_
* MIDI implementation with support for note on, note off, sustain, pitch bend, and program change messages

### Menu Control
The menu can be navigated using the rotary encoder with the actions outlined in the preceding table.

| Action                   | Parameter Unselected         | Parameter Selected           |
| ------------------------ | ---------------------------- | ---------------------------- |
| Increment (Rotate Right) | Next Parameter               | Increase Value               |
| Decrement (Rotate Left)  | Previous Parameter           | Decrease Value               |
| Click                    | Select Parameter             | Exit Selection               |
| Double Click             | Skip to Next Parameter Group | Reset Value to Initial Value |
| Long Press               | Save Current Preset          | Save Current Preset          |

## Available Programs

### [Monophonic Synthesizer](monophonic.py)
A fully parametric dual-oscillator monophonic synthesizer.

### [4-Voice Polyphonic Synthesizer](polyphonic.py)
A parametric polyphonic synthesizer with 4 voices and 1 oscillator per voice.

## Installation
Currently, installation is only detailed for linux-based devices. The installation process should be similar on Windows or Mac, but may require different command line procedures.
1. Follow the [installation guide](https://pico-synth-sandbox.readthedocs.io/en/latest/software.html) for `pico_synth_sandbox` to get your device set up with CircuitPython and all library requirements.
2. Ensure that your CircuitPython device is connected and mounted.
3. Copy this repository to your computer using `git clone https://github.com/dcooperdalrymple/pcolamakerfaire2023.git` and enter the root directory of the repository using `cd pcolamakerfaire2023`.
4. Run the default action of the provided makefile to compile shared libraries and upload them to your device by running the following command in the root directory of the repository: `make`.
5. Upload the desired program to device as `code.py` either manually or by using the provided makefile with the name of the desired program, ie: `make monophonic`. The following programs are available:
   * monophonic
   * polyphonic
6. Perform a software/hardware reset or use a REPL client such as [Thonny](https://thonny.org/) to run the program.
