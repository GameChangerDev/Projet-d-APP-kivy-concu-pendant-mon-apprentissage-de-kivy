"""Ici se trouve toutes les fonctions utilitaires diverses"""
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock

def clean(container):
    """nettoyeur de widgets"""
    container.clear_widgets()
    #print("Ecran mis à jour")
    popup = Popup(title="succès", content=Label(text='Ecran Mis à jour'), size_hint=(0.6, 0.6))
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 5)

def pipline(url):
    """Piplines"""
    with open(url, "r") as f:
        for ligne in f:
            if ligne == "" or ligne.isspace() or (not ligne):
                continue
            yield ligne.strip()
