# pcolamakerfaire2023 - menu.py
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import time, os, json
from pico_synth_sandbox import clamp, map_value, unmap_value, check_dir
from pico_synth_sandbox.display import Display
from pico_synth_sandbox.encoder import Encoder
from pico_synth_sandbox.synth import Synth
from pico_synth_sandbox.voice import Voice, AREnvelope
from pico_synth_sandbox.voice.oscillator import Oscillator
from pico_synth_sandbox.waveform import Waveform

class MenuItem:
    def __init__(self, title:str="", group:str=""):
        self._title = title
        self._group = group
        self._enabled = False
    def get(self):
        return None
    def set(self, value):
        pass
    def navigate(self, step:int) -> bool:
        return True # Indicate to move on to another item
    def previous(self) -> bool:
        return self.navigate(-1)
    def next(self) -> bool:
        return self.navigate(1)
    def increment(self) -> bool:
        return False # Indicate whether to redraw
    def decrement(self) -> bool:
        return False # Indicate whether to redraw
    def reset(self) -> bool:
        return False # Indicate whether to redraw
    def is_enabled(self) -> bool:
        return self._enabled
    def enable(self, display:Display):
        self._enabled = True
        title = ""
        if self._group:
            title += self._group
            if self._title: title += ":"
        if self._title:
            title += self._title
        if title:
            display.write(title)
    def disable(self):
        self._enabled = False
    def draw(self, display:Display):
        pass

class NumberMenuItem(MenuItem):
    def __init__(self, title:str="", group:str="", step:float=0.1, initial:float=0.0, minimum:float=0.0, maximum:float=1.0, loop:bool=False, update:function=None):
        MenuItem.__init__(self, title, group)
        self._step = step
        self._initial = initial
        self._value = initial
        self._minimum = minimum
        self._maximum = maximum
        self._loop = loop
        self._update = update
    def get(self) -> float:
        return self._value
    def get_relative(self) -> float:
        return unmap_value(self._value, self._minimum, self._maximum)
    def set(self, value:float):
        value = clamp(value, self._minimum, self._maximum)
        if self._value != value:
            self._value = value
            self._do_update()
    def increment(self) -> bool:
        if self._value == self._maximum:
            if self._loop:
                self._value = self._minimum
                return True
            else:
                return False
        self._value = min(self._value + self._step, self._maximum)
        self._do_update()
        return True
    def decrement(self) -> bool:
        if self._value == self._minimum:
            if self._loop:
                self._value = self._maximum
                return True
            else:
                return False
        self._value = max(self._value - self._step, self._minimum)
        self._do_update()
        return True
    def reset(self) -> bool:
        if self._value == self._initial:
            return False
        self._value = self._initial
        return True
    def draw(self, display:Display):
        display.write(self._value, (0,1))
    def set_update(self, callback:function):
        self._update = callback
    def _do_update(self):
        if self._update: self._update(self.get())

class BarMenuItem(NumberMenuItem):
    def __init__(self, title:str="", group:str="", step:float=1/16, initial:float=0.0, minimum:float=0.0, maximum:float=1.0, update:function=None):
        NumberMenuItem.__init__(self, title, group, step, initial, minimum, maximum, False, update)
    def enable(self, display:Display):
        display.enable_horizontal_graph()
        NumberMenuItem.enable(self, display)
    def draw(self, display:Display):
        display.write_horizontal_graph(self._value, self._minimum, self._maximum, (0,1), 16)

class ListMenuItem(NumberMenuItem):
    def __init__(self, items:tuple[str], title:str="", group:str="", loop:bool=True, update:function=None):
        NumberMenuItem.__init__(self, title, group, 1, 0, 0, len(items)-1, loop, update)
        self._items = items
    def draw(self, display:Display):
        display.write(self._items[int(self._value) % len(self._items)], (0,1))

class MenuGroup(MenuItem):
    def __init__(self, items:tuple[MenuItem], group:str="", loop:bool=False):
        MenuItem.__init__(self, group=group)
        self._items = items
        self._index = 0
        self._loop = loop

        if self._group:
            for item in self._items:
                if not issubclass(type(self.get_current_item()), MenuGroup):
                    item._group = self._group
    
    def get_current_item(self) -> MenuItem:
        return self._items[self._index]
    
    def get(self) -> tuple:
        return tuple([item.get() for item in self._items])
    def set(self, data:tuple):
        if type(data) is tuple or type(data) is list:
            for i in range(len(data)):
                if i >= len(self._items):
                    break
                self._items[i].set(data[i])
    
    def navigate(self, step:int, display:Display, force:bool=False) -> bool:
        if not force and issubclass(type(self.get_current_item()), MenuGroup) and not self.get_current_item().navigate(step, display):
            return False
        if not self._loop and ((step > 0 and self._index + step >= len(self._items)) or (step < 0 and self._index + step < 0)):
            return True
        if force or issubclass(type(self.get_current_item()), MenuGroup) or self.get_current_item().navigate(step):
            self.get_current_item().disable()
            self._index = (self._index + step) % len(self._items)
            if issubclass(type(self.get_current_item()), MenuGroup):
                self.get_current_item().enable(display, step < 0)
            else:
                self.get_current_item().enable(display)
            self.draw(display)
        return False
    def previous(self, display:Display, force:bool=False) -> bool:
        return self.navigate(-1, display, force)
    def next(self, display:Display, force:bool=False) -> bool:
        return self.navigate(1, display, force)
    def increment(self) -> bool:
        return self.get_current_item().increment()
    def decrement(self) -> bool:
        return self.get_current_item().decrement()
    def reset(self) -> bool:
        return self.get_current_item().reset()
    
    def enable(self, display:Display, last:bool = False):
        # NOTE: Don't call MenuItem.enable to avoid drawing MenuGroup
        self._enabled = True
        self._index = len(self._items) - 1 if last else 0
        if issubclass(type(self.get_current_item()), MenuGroup):
            self.get_current_item().enable(display, last)
        else:
            self.get_current_item().enable(display)
    def disable(self):
        MenuItem.disable(self)
        self.get_current_item().disable()

    def draw(self, display:Display):
        self.get_current_item().draw(display)

class AREnvelopeMenuGroup(MenuGroup):
    def __init__(self, envelope:AREnvelope, group:str=""):
        self._attack = NumberMenuItem("Attack", initial=envelope.get_attack(), maximum=2.0, update=envelope.set_attack)
        self._release = NumberMenuItem("Release", initial=envelope.get_release(), maximum=2.0, update=envelope.set_release)
        self._amount = NumberMenuItem("Amount", initial=envelope.get_amount(), step=0.05, update=envelope.set_amount)
        MenuGroup.__init__(self, (self._attack, self._release, self._amount), group)
    def enable(self, display:Display, last:bool = False):
        MenuGroup.enable(self, display, last)
        display.enable_vertical_graph()
    def draw(self, display:Display):
        attack_bars = round(map_value(self._attack.get_relative(), 1, 8))
        release_bars = round(map_value(self._release.get_relative(), 1, 8))
        amount_bars = 16 - (attack_bars + release_bars)
        amount = self._amount.get_relative()
        for i in range(attack_bars):
            display.write_vertical_graph(amount * ((i + 1) / attack_bars), position=(i,1))
        if amount_bars:
            for i in range(amount_bars):
                display.write_vertical_graph(amount, position=(attack_bars+i,1))
        for i in range(release_bars):
            display.write_vertical_graph(amount * ((i + 1) / release_bars), position=(15-i,1))

class ADSREnvelopeMenuGroup(MenuGroup):
    def __init__(self, voice:Oscillator, group:str=""):
        self._attack_time = NumberMenuItem("Attack", initial=voice._attack_time, maximum=2.0, update=voice.set_envelope_attack_time)
        self._attack_level = NumberMenuItem("Atk Lvl", initial=voice._attack_level, step=0.05, update=voice.set_envelope_attack_level)
        self._decay_time = NumberMenuItem("Decay", initial=voice._decay_time, maximum=2.0, update=voice.set_envelope_decay_time)
        self._sustain_level = NumberMenuItem("Stn Lvl", initial=voice._sustain_level, step=0.05, update=voice.set_envelope_sustain_level)
        self._release_time = NumberMenuItem("Release", initial=voice._release_time, maximum=2.0, update=voice.set_envelope_release_time)
        MenuGroup.__init__(self, (self._attack_time, self._attack_level, self._decay_time, self._sustain_level, self._release_time), group)
    def enable(self, display:Display, last:bool = False):
        MenuGroup.enable(self, display, last)
        display.enable_vertical_graph()
    def draw(self, display:Display):
        attack_bars = round(map_value(self._attack_time.get_relative(), 1, 5))
        decay_bars = round(map_value(self._decay_time.get_relative(), 1, 5))
        release_bars = round(map_value(self._release_time.get_relative(), 1, 5))
        sustain_bars = 16 - (attack_bars + decay_bars + release_bars)
        attack_level = self._attack_level.get_relative()
        sustain_level = self._sustain_level.get_relative()
        for i in range(attack_bars):
            display.write_vertical_graph(
                value = attack_level * ((i + 1) / attack_bars),
                position = (i,1)
            )
        for i in range(decay_bars):
            display.write_vertical_graph(
                value = (attack_level - sustain_level) * ((i + 1) / decay_bars) + sustain_level,
                position = (attack_bars+(decay_bars-1-i),1)
            )
        for i in range(attack_bars+decay_bars, attack_bars+decay_bars+sustain_bars):
            display.write_vertical_graph(sustain_level, position=(i,1))
        for i in range(release_bars):
            display.write_vertical_graph(
                value = sustain_level * ((i + 1) / release_bars),
                position = (15-i,1)
            )

class VoiceMenuGroup(MenuGroup):
    def __init__(self, voice:Voice, synth:Synth, items:tuple[MenuItem]=None, group:str=""):
        self._voice = voice
        self._synth = synth
        _items = (
            BarMenuItem("Level", initial=1.0, update=voice.set_level),
            BarMenuItem("Velocity", initial=0.0, update=voice.set_velocity_amount),
            ListMenuItem(("Low Pass", "High Pass", "Band Pass"), "Filter Type", update=self._update_filter_type),
            BarMenuItem("Filter Freq", initial=1.0, step=0.05, update=self._update_filter_frequency),
            BarMenuItem("Filter Reso", update=self._update_filter_resonance)
        )
        if items: _items = (_items + items)
        MenuGroup.__init__(self, _items, group)
    def _update_filter_type(self, value:float):
        self._voice.set_filter_type(int(value), self._synth)
    def _update_filter_frequency(self, value:float):
        self._voice.set_filter_frequency(value, self._synth)
    def _update_filter_resonance(self, value:float):
        self._voice.set_filter_resonance(value, self._synth)

class OscillatorMenuGroup(VoiceMenuGroup):
    def __init__(self, voice:Oscillator, synth:Synth, group:str=""):
        VoiceMenuGroup.__init__(self, voice, synth, (
            BarMenuItem("Glide", update=voice.set_glide),
            BarMenuItem("Pitch Bend", step=1/8, minimum=-1.0, update=voice.set_pitch_bend_amount),
            BarMenuItem("Course Tune", step=1/12, minimum=-2.0, maximum=2.0, update=voice.set_coarse_tune),
            BarMenuItem("Fine Tune", step=1/12/16, minimum=-1/12, maximum=1/12, update=voice.set_fine_tune),
            ListMenuItem(("Square", "Sawtooth", "Sine", "Noise", "Sine Noise"), "Waveform", update=self._update_waveform),
            BarMenuItem("Tremolo Rate", maximum=4.0, update=voice.set_tremolo_rate),
            BarMenuItem("Tremolo Depth", step=1/64, maximum=0.5, update=voice.set_tremolo_depth),
            BarMenuItem("Vibrato Rate", maximum=4.0, update=voice.set_vibrato_rate),
            BarMenuItem("Vibrato Depth", step=1/64, maximum=0.5, update=voice.set_vibrato_depth),
            BarMenuItem("Pan", step=1/8, minimum=-1.0, update=voice.set_pan),
            BarMenuItem("Pan Rate", maximum=4.0, update=voice.set_pan_rate),
            BarMenuItem("Pan Depth", update=voice.set_pan_depth),
            ADSREnvelopeMenuGroup(voice, group=group+"AEnv"),
            BarMenuItem("Fltr LFO Rate", maximum=4.0, update=voice.set_filter_lfo_rate),
            BarMenuItem("Fltr LFO Depth", step=1/64, maximum=0.5, update=voice.set_filter_lfo_depth),
            AREnvelopeMenuGroup(voice._filter_envelope, group=group+"FEnv")
        ), group)
    def _update_waveform(self, value:float):
        value = int(value)
        waveform = None
        if value == 0:
            waveform = Waveform.get_square()
        elif value == 1:
            waveform = Waveform.get_saw()
        elif value == 2:
            waveform = Waveform.get_sine()
        elif value == 3:
            waveform = Waveform.get_noise()
        elif value == 4:
            waveform = Waveform.get_sine_noise()
        if waveform:
            self._voice.set_waveform(waveform)

class Menu(MenuGroup):
    def __init__(self, items:tuple, group:str = "", write:function=None):
        MenuGroup.__init__(self, items, group, loop=True)

        self._selected = False
        self._write = write

        self._display = Display()
        self._encoder = Encoder()

        self._display.clear()
        self._display.set_cursor_position(0,0)
        self._display.hide_cursor()
        self._display.write("PicoSynthSandbox", (0,0))
        self._display.write("Loading...", (0,1))

    def ready(self):
        self._display.clear()
        self._index = 0
        self.draw()
        self.enable()

    def enable(self):
        self._encoder.set_click(self.encoder_click)
        self._encoder.set_double_click(self.encoder_double_click)
        self._encoder.set_long_press(self.encoder_long_press)
        self._encoder.set_increment(self.encoder_increment)
        self._encoder.set_decrement(self.encoder_decrement)
        MenuGroup.enable(self, self._display)
    def disable(self):
        self._encoder.set_click(None)
        self._encoder.set_double_click(None)
        self._encoder.set_long_press(None)
        self._encoder.set_increment(None)
        self._encoder.set_decrement(None)
        MenuGroup.disable(self)

    def encoder_click(self):
        self._selected = not self._selected
        self._display.set_cursor_enabled(self._selected)
        self._display.set_cursor_blink(self._selected)
    def encoder_double_click(self):
        if self._selected:
            if self.reset():
                self.draw()
        else:
            self.next(force=True)
    def encoder_long_press(self):
        self.disable()
        self._display.clear()
        self._display.write("Saving...")
        if self._write:
            self._write()
        else:
            self.write()
        self._display.write("Complete!")
        time.sleep(0.5)
        self.enable()
        self.draw()
    def encoder_increment(self):
        if self._selected:
            if self.increment():
                self.draw()
        else:
            self.next()
    def encoder_decrement(self):
        if self._selected:
            if self.decrement():
                self.draw()
        else:
            self.previous()

    def navigate(self, step:int, display:Display=None, force:bool=False):
        if not display: display=self._display
        MenuGroup.navigate(self, step, display, force)
    def previous(self, display:Display=None, force:bool=False):
        if not display: display=self._display
        MenuGroup.previous(self, display, force)
    def next(self, display:Display=None, force:bool=False):
        if not display: display=self._display
        MenuGroup.next(self, display, force)
    def draw(self, display:Display=None):
        if not display: display=self._display
        MenuGroup.draw(self, display)

    def update(self):
        self._encoder.update()

    def write(self, name:str="", dir:str="/presets") -> bool:
        if not name: name = self._group
        if not name: return False

        data = self.get()
        if not data: return False

        path = "{}/{}.json".format(dir, name)

        result = False
        try:
            check_dir(dir)
            with open(path, "w") as file:
                json.dump(data, file)
            print("Successfully written JSON file: {}".format(path))
            result = True
        except:
            print("Failed to write JSON file: {}".format(path))
        return result
    def set_write(self, callback:function):
        self._write=callback
    
    def read(self, name:str="", dir:str="/presets") -> bool:
        if not name: name = self._group
        if not name: return False

        path = "{}/{}.json".format(dir, name)
        try:
            os.stat(path)
        except:
            print("Failed to read JSON file, doesn't exist: {}".format(path))
            return False

        data = None
        try:
            with open(path, "r") as file:
                data = json.load(file)
            print("Successfully read JSON file: {}".format(path))
        except:
            print("Failed to read JSON file: {}".format(path))

        if not data:
            return False
        
        self.set(data)
        return True
