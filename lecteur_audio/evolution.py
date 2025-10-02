from functools import wraps

import kivy
kivy.require("2.3.1")
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.app import App, runTouchApp
from kivy.graphics import Rectangle, RoundedRectangle, Color
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.core.window import Window
from kivy.core.audio import Sound
from kivy.metrics import dp
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from random import random
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import BooleanProperty, ObjectProperty


def normalise_buttons(reference=ToggleButton, button_list=[]):
    """Fermer les autres options du menu et Laisser uniquement celui qui est en cours"""
    for but in button_list:
        if but is reference:
            if reference.state == "down":
                liste:list = button_list.copy()
                btn_delet = liste.pop(liste.index(but))
                for btn in liste:
                     btn.state = "normal"
            break

class Progress(ProgressBar):
    """barre de progréssion manipulable"""
    son = ObjectProperty(None)# son qui sera manipulé lorsqu'on change bourge la Barre

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.set_value(touch.x)
            return True
        return

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.set_value(touch.x)
            return True
        return

    def on_touch_up(self, touch):
        touch.ungrab(self)
        return True

    def set_value(self, x):
        pos_ratio = max(self.x, min(self.right, x)) - self.x
        value = pos_ratio/float(self.width)
        self.value = value
        self.son.seek(value * self.son.length)


class PersoFloat(FloatLayout, Button):
    pass

class PersonBox(BoxLayout, Button):
    pass

class PersoGrid(GridLayout, Button):
    pass

class PersoScatter(ScatterLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.80, 0.40)
        #self.pos_hint = {"center_x": 0.5, "center_y": 0.5}

class Evolution(BoxLayout, Button):
    """gerer et afficher l'évolution du son"""
    changement = BooleanProperty(False)
    trigger_evolution = ObjectProperty(None, allow_none=True)

    def __init__(self, son:Sound, **kwargs):
        super().__init__(**kwargs)
        self.son = son
        self.orientation = 'vertical'
        self.size_hint = (0.90, 0.90)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.spacing = dp(10)
        self.padding = [dp(10) for i in range(4)]
        self.background_color = (0, 0, 1, 1)

        if self.son is not None:
            min_, value_, max_ = 0, self.son.get_pos()/self.son.length , 1
            self.box_ev = PersonBox(orientation='vertical', background_color = (1, 0, 0, 0.75))
            self.evolution = Progress(son=self.son, max=1, value=(value_/max_))# Barre de progréssion manipulable
            self.box_ev.add_widget(self.evolution)

        self.box_ar = PersoFloat(background_color=(0, 1, 0, 1))
        self.btn_fermer = Button(size_hint_y=0.2, text="Fermer", font_size=18)

        self.avance = Button(
            background_normal=r"png_boutons\avance30_2.png", size_hint = (None, None),
            background_down=r"png_boutons\avance30_2.png",
            size=(64, 64),
            pos_hint={'center_x': 0.75, 'center_y': 0.5}
        )

        self.recule = Button(
            background_normal=r"png_boutons\recule30_2.png",
            background_down=r"png_boutons\recule30_2.png",
            size_hint=(None, None), size=(64, 64),
            pos_hint={'center_x': 0.25, 'center_y': 0.5}
        )
        # liaisons
        self.avance.bind(on_press=lambda *args: self.avance30())
        self.recule.bind(on_press=lambda *args: self.recule30())
        self.btn_fermer.fbind('on_press', self.fermer_btn)#lambda inst: self.parent.remove_widget(self))

        self.box_ar.add_widget(self.recule)
        self.box_ar.add_widget(Label())
        self.box_ar.add_widget(self.avance)

        self.add_widget(self.box_ev)
        self.add_widget(self.box_ar)
        self.add_widget(self.btn_fermer)

        Clock.schedule_interval(self.react_color, 0.3)
        Clock.schedule_interval(self.react_color_evolution, 0.6)
        Clock.schedule_interval(self.react_color_ar, 0.9)

        # Déplacer la Slide barre
        Clock.schedule_interval(self.react_slider, 0.1)

    def fermer_btn(self, inst):
        """Passe l'état du toggle button qui permet l'affichage de evolution à normal"""
        self.trigger_evolution.state = "normal"

    def ajuste_max(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.emplacement(self.son.get_pos()) > 0.993:
                func(self, *args, *kwargs)
                if self.evolution.value > 0.993:
                    self.evolution.value = 1
                    self.changement = True
            else:
                func(self, *args, **kwargs)
                self.changement = False
        return wrapper


    def react_color(self, dt):
        self.background_color = (random(), random(), random(), 1)

    @ajuste_max
    def avance30(self):
        if self.emplacement(self.son.get_pos()) < 1:
            self.son.seek(self.son.get_pos() + 30)

    @ajuste_max
    def recule30(self):
        if self.emplacement(self.son.get_pos()) < 1:
            self.son.seek(self.son.get_pos() - 30)

    def react_color_evolution(self, dt):
        self.box_ev.background_color = (random(), random(), random(), 1)

    def react_color_ar(self, dt):
        self.box_ar.background_color = (random(), random(), random(), 1)

    @ajuste_max
    def react_slider(self, dt):
        self.evolution.value = self.emplacement(self.son.get_pos())
        if self.evolution.value == 1:
            print('max', self.evolution.max)

    def emplacement(self, current_pos):
        return current_pos/self.son.length