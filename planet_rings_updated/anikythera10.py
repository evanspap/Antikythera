# File: anikythera10.py
# Updated AntikytheraRings with distinct rotating image rings per celestial body

import astronomy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.image import Image as CoreImage
from kivy.graphics import Rectangle, PushMatrix, PopMatrix, Rotate, Translate, ClearBuffers, ClearColor
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

NAMES = ["moon", "mercury", "venus", "sun", "mars", "jupiter", "saturn"]
BODIES = [
    astronomy.Body.Moon,
    astronomy.Body.Mercury,
    astronomy.Body.Venus,
    astronomy.Body.Sun,
    astronomy.Body.Mars,
    astronomy.Body.Jupiter,
    astronomy.Body.Saturn,
]

class AntikytheraRings(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ring_textures = [CoreImage(f'ring_{name}.png').texture for name in NAMES]
        self.angles = [0] * len(NAMES)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        w, h = self.width, self.height
        disk_size = min(w, h)
        x0 = (w - disk_size) / 2
        y0 = (h - disk_size) / 2
        center = (x0 + disk_size / 2, y0 + disk_size / 2)

        # Adjust each texture radius to match expected scale
        radius_px = [270, 307, 345, 395, 432, 470, 510]  # from center
        base_max = max(radius_px)

        with self.canvas:
            ClearColor(1, 1, 1, 1)
            ClearBuffers()

            for i, angle in enumerate(self.angles):
                tex = self.ring_textures[i]
                scale = (radius_px[i] * 2) / tex.width * (disk_size / (2 * base_max))
                size = tex.width * scale
                PushMatrix()
                Translate(*center)
                Rotate(angle=-angle, origin=(0, 0))
                Rectangle(texture=tex,
                          pos=(-size / 2, -size / 2),
                          size=(size, size))
                PopMatrix()

class SplitCanvasApp(App):
    def build(self):
        root = BoxLayout()
        display = AntikytheraRings()
        sliders_area = BoxLayout(orientation='vertical', padding=5, spacing=5)

        now = datetime.utcnow()
        dt_min = now - timedelta(days=365.25*100)
        dt_max = now + timedelta(days=365.25*100)
        min_days = -int((now - dt_min).days)
        max_days = int((dt_max - now).days)
        date_slider = Slider(min=min_days, max=max_days, value=0, size_hint=(0.55, 1))
        date_input = TextInput(text=now.strftime('%Y-%m-%d %H:%M'), size_hint=(0.45, 1), multiline=False, halign='center', font_size='16sp')
        date_label = Label(text='UTC Date/Time:', size_hint=(0.25,1), font_size='16sp', color=(0,0,0,1))

        def update_angles_from_dt(dt):
            t = astronomy.Time.Make(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            for idx, body in enumerate(BODIES):
                geo_vec = astronomy.GeoVector(body, t, aberration=True)
                ecl = astronomy.Ecliptic(geo_vec)
                display.angles[idx] = ecl.elon

        def on_date_slider(instance, value):
            new_dt = now + timedelta(days=float(value))
            date_input.text = new_dt.strftime('%Y-%m-%d %H:%M')
            update_angles_from_dt(new_dt)
            display.update_canvas()
        date_slider.bind(value=on_date_slider)

        def on_date_input_validate(instance):
            try:
                entered = datetime.strptime(instance.text, '%Y-%m-%d %H:%M')
                days_offset = (entered - now).total_seconds() / (24*3600)
                date_slider.value = days_offset
                update_angles_from_dt(entered)
                display.update_canvas()
            except Exception:
                instance.text = (now + timedelta(days=float(date_slider.value))).strftime('%Y-%m-%d %H:%M')
        date_input.bind(on_text_validate=on_date_input_validate)

        def shift_by(years=0, months=0, days=0):
            current_dt = datetime.strptime(date_input.text, '%Y-%m-%d %H:%M')
            new_dt = current_dt + relativedelta(years=years, months=months, days=days)
            date_input.text = new_dt.strftime('%Y-%m-%d %H:%M')
            date_slider.value = (new_dt - now).total_seconds() / (24*3600)
            update_angles_from_dt(new_dt)
            display.update_canvas()

        def set_now():
            current = datetime.utcnow()
            date_input.text = current.strftime('%Y-%m-%d %H:%M')
            date_slider.value = (current - now).total_seconds() / (24*3600)
            update_angles_from_dt(current)
            display.update_canvas()

        date_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=6)
        date_row.add_widget(date_label)
        date_row.add_widget(date_slider)
        date_row.add_widget(date_input)

        date_controls = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=4)
        for label, kwargs in [
            ("Now", None),
            ("-Day", dict(days=-1)), ("+Day", dict(days=1)),
            ("-Month", dict(months=-1)), ("+Month", dict(months=1)),
            ("-Year", dict(years=-1)), ("+Year", dict(years=1)),
            ("-Decade", dict(years=-10)), ("+Decade", dict(years=10))]:
            b = Button(text=label, size_hint=(None, 1), width=70)
            if kwargs is None:
                b.bind(on_release=lambda inst: set_now())
            else:
                b.bind(on_release=lambda inst, kw=kwargs: shift_by(**kw))
            date_controls.add_widget(b)

        sliders_area.add_widget(date_row)
        sliders_area.add_widget(date_controls)
        root.add_widget(display)
        root.add_widget(sliders_area)
        Window.bind(size=lambda w,s: self.adjust_layout(root, display, sliders_area, s))
        self.adjust_layout(root, display, sliders_area, Window.size)
        update_angles_from_dt(now)
        display.update_canvas()
        return root

    def adjust_layout(self, root, display, sliders, size):
        w, h = size
        if h > w:
            root.orientation = 'vertical'
            display.size_hint = (1, 0.5)
            sliders.size_hint = (1, 0.5)
        else:
            root.orientation = 'horizontal'
            display.size_hint = (0.5, 1)
            sliders.size_hint = (0.5, 1)

if __name__ == '__main__':
    SplitCanvasApp().run()
