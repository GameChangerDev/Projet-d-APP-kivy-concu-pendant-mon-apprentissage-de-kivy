#:Projet : Lecteur audio
# créer une Application de lecture audio complete avec un bouton_play,
# une barre d'action pour avancer, reculer, stopper et résumer l'audio

from kivy.app import App
from kivy.properties import (
    NumericProperty, BooleanProperty, StringProperty,
    ColorProperty, ListProperty, ObjectProperty, DictProperty
)
from django
from kivy.clock import Clock
from kivy.uix.actionbar import ActionBar, ActionView, ActionPrevious, ActionButton, ActionOverflow, ActionToggleButton
from kivy.core.text import LabelBase
from kivy.core.audio import Sound, SoundLoader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.label import Label
from kivy.config import ConfigParser
from random import choice
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scatter import Scatter
from kivy.uix.dropdown import DropDown
from kivy.uix.slider import Slider
from kivy.lang import Builder
import json
from datetime import datetime
from functools import wraps
import time
import os
import sys
from kivy.resources import resource_add_path
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.animation import Animation, Sequence
from random import random, randint
from kivy.uix.slider import Slider
from evolution import PersonBox, Evolution, PersoScatter, normalise_buttons
from kivy.storage.jsonstore import JsonStore
from kivy.uix.widget import Widget
from folder_adder import popup_chooser, validate_btn, file_chooser, FilesParser
from kivy.uix.popup import Popup
from utils import pipline, clean

class Box(BoxLayout):
    pass

racine = Builder.load_file("kv_files/lecteur_audio.kv")

def smart_close(widget:Widget, touch, trigger):
    """ferme le widget quand on double clic dessus"""
    if touch.is_triple_tap:
        widget.parent.remove_widget(widget)
        trigger.state = "normal"

class LecteurAudioApp(App):
    # variables de classe (propriétés)
    menu = ObjectProperty(None, allownone=True)
    bouton_play = ObjectProperty(None, allownone=True)
    musiclist:list=[]
    music_on =""
    music_on_param = StringProperty('')# le son initiale du next des paramètre
    son=''
    index_sound_on = NumericProperty()
    buttonsoundlist = []
    next_settings = BooleanProperty(False)
    parent_folders = ListProperty([url for url in pipline("folders.txt")])
    files_list = ListProperty([])
    music_dict = {}
    structure_lf = DictProperty({})
    bouton_menu = ObjectProperty(None)
    barre_volume = ObjectProperty(None)
    valeur_slider = NumericProperty()
    box_bvolume = ObjectProperty()
    box_label_volume = ObjectProperty()
    label_bvolume = ObjectProperty()
    imax_v = ObjectProperty()
    imin_v = ObjectProperty()
    volume_move = NumericProperty() # variation de volume
    volume = ObjectProperty()
    parametre = ObjectProperty()
    evolution = ObjectProperty()
    fin_son = BooleanProperty()
    chrono_fin = ObjectProperty(None, allownone=True)
    ferme_son_auto = BooleanProperty(False)
    boutons = ListProperty()
    menu_evolution = ObjectProperty()
    options_son = JsonStore("options_son.json")
    lastsound = StringProperty()

    scroll = ScrollView(
        bar_width=15,
        bar_color=[0, 0, 1, 1],
        bar_inactive_color=[1, 0.8, 0.2, 1]
    )

    def build(self):
        # disposition dispersée du bouton de menu
        layout_params = ScatterLayout(pos=(Window.width/8, Window.height/2), size_hint=(0.22, 0.05))

        # liste de musique
        self.musiclist:list =[]

        # construire les fichiers
        self.build_files()
        #self.musiclist = [os.path.join(self.parent_folder, file_name) for file_name in self.file_list]

        # jouer la musique aléatoirement ou le dernier lors de la séssion précédente
        for music in self.musiclist:
            if self.options_son.get("options_son")["lastsound"] in music:
                self.lastsound = music
                break

        if self.musiclist:
            self.music_on = choice(self.musiclist) if  self.lastsound == "" else self.lastsound
        else:
            pass

        # reprendre le son là ou on la laisser
        if self.lastsound or self.musiclist:
            if self.options_son.get('options_son')["duree"] > 0:
                self.son = SoundLoader.load(self.lastsound)
                if self.son is not None:
                    self.son.seek(self.options_son.get('options_son')["duree"])
                    self.son.volume = self.options_son.get('options_son')["volume"]

        self.box = Box(
            size_hint_y=None,
            padding=[10, 5, 30, 5],
            spacing=7.5
        )
        self.box.bind(minimum_height=self.box.setter("height"))

        # créer la liste de sont
        self.built_soundlist()

        # ajouter tout les sont disponible dans une liste à l'ecran avec un scroll
        self.scroll.add_widget(self.box)
        Window.add_widget(self.scroll)

        # lier le bouton pause/play
        self.bouton_play = racine.ids["bascule"]
        self.bouton_play.bind(state=self.jouer_son)

        # menu deroulant
        self.menu = DropDown()
        self.menu.container.spacing = 5

        # Bouton paramètre libre
        self.bouton_menu = Button(
            on_release=self.menu.open,
            background_normal="png_boutons/parametre3.png",
            background_down="png_boutons/parametre3.png",
            size_hint =(None, None),
            size=(48, 48),
            x=50
        )

        # Bouton pour voir les evolutions
        self.evolution = ToggleButton(
            background_normal="png_boutons/evolution.png",
            background_down="png_boutons/evolution2.png",
            size_hint=(None, None),
            size=(48, 48),
            on_release=lambda btn: self.menu.select(data=self.evolution)
        )

        # Bouton pour ajouter un repertoire par l'interface user
        self.ajout = ToggleButton(
            background_normal="png_boutons/ajout2_48_48.png",
            background_down="png_boutons/ajout48_48.png",
            size_hint=(None, None),
            size=(48, 48),
            on_release = lambda btn: self.menu.select(data=self.ajout)
        )

        # boutons pour le menu
        self.volume = ToggleButton(
            background_normal="png_boutons/VOLUME.png",
            background_down="png_boutons/VOLUME2.png",
            size_hint=(None, None),
            size=(48, 48),
            on_release=lambda btn: self.menu.select(self.volume)
        )

        self.valeur_slider = self.config.getfloat("Parametres de son", "volume")

        self.parametre = ToggleButton(
            background_normal="png_boutons/parametre3.png",
            background_down="png_boutons/parametre3.png",
            size_hint=(None, None),
            size=(48, 48),
            on_release=lambda btn: self.menu.select(data=self.parametre)
        )
        #lier le changement d'état du bouton paramètre dans le menu
        self.evolution.bind(state=self.reacts_evolution)
        self.ajout.bind(state=self.reacts_ajout)
        self.parametre.bind(state=self.reactions_params)
        self.volume.bind(state=self.reacts_volume_param)

        # ajouter les boutons au menu
        self.menu.add_widget(self.evolution)
        self.menu.add_widget(self.ajout)
        self.menu.add_widget(self.volume)
        self.menu.add_widget(self.parametre)

        # Binder le on_select du menu
        self.menu.bind(on_select=self.on_select)

        layout_params.add_widget(self.bouton_menu)
        Window.add_widget(layout_params)


        # créer une police personnalisée
        LabelBase.register(name='arial', fn_regular="arial.ttf")
        print()
        return racine

    def build_files(self):
        # Récuperez les fichiers
        for index, nom in enumerate(self.parent_folders):
            for file in os.listdir(nom):
                self.musiclist.append(os.path.join(nom, file))
                if os.listdir(nom)[-1] == file:
                    self.structure_lf[index + 1] = (nom.split("\\")[-1], os.listdir(nom).index(file), file)

    def built_soundlist(self):
        """Construire la les boutons de sons pour la lites de musique"""
        # liste de boutons de sons
        for index, sound in enumerate(self.musiclist):
            son = Button(
                text=f"{index + 1}. {self.nom_son(sound)}",
                size_hint=(1, 0.1),
                size_hint_y=None,
                height=50
            )
            son.bind(on_press=self.play_sound_list)
            self.boutons.append(son)

            self.buttonsoundlist.append(son)
            self.box.add_widget(son)

            for key, valeur in self.structure_lf.items():
                if valeur[2] in sound:
                    label_album = Label(text=valeur[0], size_hint_y=None, height=100, bold=True)
                    self.box.add_widget(label_album)

    def on_select(self, inst, data:ToggleButton):
        """Gérer l'lévénement on_select du menu"""
        if data is not self.ajout:
            self.bouton_menu.background_down = data.background_down

    def on_start(self):
        # on repasse les Suivant et Precedent des paramètres à 0
        self.config.set("Parametres de son", "Next", "0")
        self.config.set("Parametres de son", "Preview", "0")

    def couleur_son(self, son, auto=False):
        """Gère l'apparence du bouton du son en cours de lecture """
        bouton = self.buttonsoundlist[self.musiclist.index(son.source)] # Bouton du son en cours

        def couleur():
            """Génère une couleur aléatoire pour le bouton du son en cours"""
            bouton.background_color = (random(), random(), random(), random())


        def animation(dt):
            """Créer l'animation séquentielle pour l'aller e retour du bouton de son en cours de lecture"""
            anim1 = Animation(x=20, d=0.1, t="in_out_bounce")
            anim2 = Animation(x=-10, d=0.1, t="in_out_bounce")
            self.seq = Sequence(anim1, anim2)
            self.seq.start(bouton)

        anim_clock = Clock.schedule_interval(animation, 0.3) # mise à jour de l'animation

        if bouton:
            self.couleur_depart = bouton.background_color
            clock = Clock.schedule_interval(lambda  dt: couleur(), 0.1)

        def neutre(*args):
            """ramener le bouton du son en cours avec c'est propriétés de départ"""
            bouton.background_color = self.couleur_depart
            anim_clock.cancel() # arrêter l'animation
            clock.cancel()
            # Remettre le bouton à son point x initial quand la musique s'arrête
            for btn in self.boutons:
                btn.x = 10

        # liaison du on_stop du son
        son.on_stop = neutre

    def reacts_ajout(self, inst, state):
        """Gère toutes les réactions sur le bouton ajout"""
        # completion des inputs du popup de selection de fichiers
        popup_chooser.music_list = self.musiclist
        popup_chooser.builder_ui = self.built_soundlist
        popup_chooser.box = self.box
        popup_chooser.scroll = self.scroll
        popup_chooser.build_sound = self.built_soundlist
        popup_chooser.menu_ajout = self.ajout
        popup_chooser.parentfolders = self.parent_folders
        popup_chooser.build_files = self.build_files

        if state == "down":
            self.bouton_menu.background_down = inst.background_down
            popup_chooser.open()

    def reacts_evolution(self, instance, state):
        """gère toute les réactionns du bouton evolution dans le menu deroulant"""
        if state == "down":
            normalise_buttons(reference=instance, button_list=self.menu.container.children)
            self.bouton_menu.background_normal = instance.background_down
            self.box = PersoScatter()
            self.menu_evolution = Evolution(self.son)
            self.menu_evolution.evolution.son = self.son
            self.menu_evolution.bind(on_touch_down=lambda inst, touch: smart_close(self.menu_evolution, touch, instance))
            self.menu_evolution.trigger_evolution = self.evolution # le bouton qui permet d'ajouter la visualisation à l'écran
            Clock.schedule_interval(self.check_changement, 1)
            self.box.add_widget(self.menu_evolution)
            Window.add_widget(self.box)
        else:
            self.bouton_menu.background_normal = instance.background_normal
            if self.box:
                try:
                    self.box.parent.remove_widget(self.box)
                except Exception as e:
                    print(e)

    def check_changement(self, dt):
        if (not self.son.loop)  and self.menu_evolution.changement:
            self.avance_auto()
            self.menu_evolution.son = self.son
            self.menu_evolution.changement = False
            self.couleur_son(self.son)

    def reactions_params(self, instance, state):
        """Gère toutes les réactions du bouton paramètres"""
        if state == "down":
            normalise_buttons(instance, self.menu.container.children)
            self.open_settings()
            self.menu.dismiss()
            self.bouton_menu.background_normal = instance.background_normal
        else:
            self.close_settings()

    def reacts_volume_param(self, instance, state):
        """gère toute les réactionns du bouton volume dans le menu deroulant"""
        if state == "down":
            normalise_buttons(instance, self.menu.container.children)
            self.bouton_menu.background_normal = instance.background_normal
            self.box_bvolume = PersonBox(
                orientation="vertical", size_hint=(0.5, None), spacing=5,
                height=100,pos_hint=({"top":0.5}),
                background_color = (0, 0, 1, 1)
            )
            self.box_bvolume.bind(on_touch_down=lambda inst, touch: smart_close(self.box_bvolume, touch, instance))
            self.box_label_volume = BoxLayout(orientation="horizontal")
            self.label_bvolume = Label(text=str(self.valeur_slider))
            self.imax_v = Label(text="100", width=60, bold=True)
            self.imin_v = Label(text="0", width=60, bold=True)
            self.barre_volume = Slider(min=0.00, max=1, value=self.valeur_slider if not self.volume_move else self.volume_move, step=0.01)
            if self.volume_move > 0:
                self.barre_volume.value = self.volume_move
            barre = self.barre_volume
            #barre.size_hint=(0.5, None)
            barre.height=48
            barre.x = 100
            #print(self.valeur_slider)# test
            self.barre_volume.bind(value=self.reglage_volume)
            # changer l'image du bouton de menu
            self.bouton_menu.background_normal = "png_boutons/VOLUME2.png"

            # box de label
            self.box_label_volume.add_widget(self.imin_v)
            self.box_label_volume.add_widget(self.label_bvolume)
            self.box_label_volume.add_widget(self.imax_v)

            # box de volume
            self.box_bvolume.add_widget(self.box_label_volume)
            self.box_bvolume.add_widget(self.barre_volume)
            Window.add_widget(self.box_bvolume)
        else:
            Window.remove_widget(self.box_bvolume)
            self.bouton_menu.background_normal = "png_boutons/VOLUME.png"

    def reglage_volume(self, instance, value):
        """Gère les changements de valeurs de la barre de volume"""
        self.son.volume = value
        self.config.set("Parametres de son", "volume", str(value))
        # mettre à jour les valeurs des labels de volume correspondants
        self.label_bvolume.text = str(value*100)
        self.config.write()

    def arret_son(func):
        @wraps(func)
        def wrapper(self, instance, *args):
            if self.son:
                self.son.stop()
            func(self, instance, *args)
            if self.evolution.state == "normal" and self.bouton_play.state == "down":
                self.evolution.state = "down"
            self.menu_evolution.son  = self.son
        return wrapper

    def parcours_list(self):
        """Gère le chargement du prochain son en tenant compte de la position du son qui vient de finir dans la liste"""
        last_index = len(self.musiclist)
        music = self.son.source
        music_suivante = self.musiclist.index(music)+1
        if music_suivante in range(last_index):
            self.music_on = self.musiclist[music_suivante]
            return self.music_on
        else:
            self.music_on = self.musiclist[0]
            return self.music_on

    def avance_auto(self, *args):
        """avance dans la liste de musique quand le son finit"""
        if self.bouton_play.state == "down":
            self.son.stop()
            self.music_on = self.verif_son()
            self.son = SoundLoader.load(self.music_on)
            if self.son:
                self.son.play()
    @arret_son
    def jouer_son(self, btn, value):
        """Gère les interaction avec le bouton play/stop"""
        if value=="down":
            if self.son:
                self.bouton_play.icon= 'png_boutons/OUVERT.png'
                if not self.son.play():
                    self.son.play()
                self.couleur_son(self.son)  # colorier le son en cours dans la liste
                self.son.volume=self.config.getfloat("Parametres de son", "Volume")
            else:
                print("Erreur sur le fichier !!")
        else:
            self.son.stop()
            self.bouton_play.icon = 'png_boutons/FERME.png'
            try:
                self.menu_evolution.btn_fermer.dispatch("on_press")
            except:
                pass

    @arret_son
    def aller_avant_param(self, dt):
        self.music_on = self.verif_son()
        self.son = SoundLoader.load(self.music_on)
        self.menu_evolution.son = self.son
        self.couleur_son(self.son)# colorier le son en cours dans la liste
        self.menu_evolution.son = self.son
        self.son.play()

        self.son = SoundLoader.load(self.musiclist[0])

    @arret_son
    def aller_avant(self, instance):
        if self.son.state == "play":
            self.son.stop()
        self.parcours_list()
        self.son = SoundLoader.load(self.music_on)
        self.couleur_son(self.son)  # colorier le son en cours dans la liste

        self.son.play()
        self.bouton_play.state = "down"

    @arret_son
    def retour_arriere(self, instance):
        self.music_on = self.verif_son(0)
        self.son = SoundLoader.load(self.music_on)
        self.menu_evolution.son = self.son
        if self.son:
            self.couleur_son(self.son)  # colorier le son en cours dans la liste
            self.son.play()
        self.bouton_play.state = "down"

    def verif_son(self, av_rec:int=1):
        if self.son:
            self.son.stop()
        ancien = self.music_on

        if av_rec == 1:
            if (self.musiclist.index(ancien) + 1) <= len(self.musiclist):
                self.index_sound_on = self.musiclist.index(ancien) + 1
                nouvel = self.musiclist[self.index_sound_on]
                return nouvel
            else:
                nouvel = self.musiclist[0]
                return nouvel
        else:
            if not (self.musiclist.index(ancien) - 1) < 0:
                self.index_sound_on = self.musiclist.index(ancien) -1
                nouvel = self.musiclist[self.index_sound_on]
                return nouvel
            else:
                nouvel = self.musiclist[0]
                return nouvel

    def nom_son(self, filename:str):
        if filename.rfind(']') != -1:
            return filename[filename.rfind("]")+1:]
        return filename[filename.rfind("-")+1:]

    @arret_son
    def play_sound_list(self, btn):
        """Joue le son sur lequel on a cliqué"""
        # récuperation d'indice
        indice = int(btn.text.split('.')[0]) - 1
        self.music_on = self.musiclist[indice]
        self.son = SoundLoader.load(self.musiclist[indice])
        self.couleur_son(self.son)
        self.son.play()
        self.bouton_play.state = "down"
        if isinstance(self.menu_evolution, (BoxLayout, Button)):
            self.menu_evolution.son = self.son

    #configuration de l'app
    def get_application_name(self):
        return "Lecteur Audio"
    def get_application_icon(self):
        return "png_boutons/FERME.png"

    def open_settings(self, *largs):
        print("paramètre ouvert avec succès")
        if self.barre_volume:
            self.volume.state="normal"
        super().open_settings(largs)

    # on crée les données dans fichier de config
    def build_config(self, config):
        config.setdefaults("Parametres de son", {"Volume": 1.0, "Next": False, "Preview": False})

    # crée les paramtres
    def build_settings(self, settings):
        settings.add_json_panel("Paramètres de son", config=self.config, filename="build_settings.json")

    def on_config_change(self, config, section, key, value):
        if key == "volume":
            self.son.volume = float(value)
            self.volume.dispatch("on_release")
            self.volume_move = float(value)

        # Changer le son en passant par les paramètres
        elif key == "Next":
            n = False if value == "0" else True
            if n is True:
                self.aller_avant(None)

        elif key == "Preview":
            if value == "1":
                self.retour_arriere(None)
                config.set("Parametres de son", key, "0")
        print(f"modification de {section}, {key} : en {value}")

    def close_settings(self, *largs):
        print("Paramètres fermé !!")
        try:
            self.volume.state = "down"
            self.box_bvolume.opacity = 0
            self.barre_volume.value = self.config.getfloat("Parametres de son", "volume")
            self.volume.state = "normal"
        except:
            self.bouton_menu.dispatch("on_release")
            self.volume.dispatch("on_press")
            print('fait')

        super().close_settings(largs)

    def on_stop(self):
        # remplir le fichier de l'options_son.json
        try:
            self.options_son.put('options_son', lastsound=self.nom_son(self.son.source), duree=self.son.get_pos(), volume=self.son.volume)
        except Exception as e:
            popup = Popup(title="succès", content=Label(text='Ecran Mis à jour'), size_hint=(0.6, 0.6))
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 5)

        with open("last_sound.txt", "a+") as f:
            f.write(self.music_on.replace('é', "e") + " " + datetime.now().isoformat() + "\n")

        #crée un petit dictionnaire
        self.music_dict = {}
        for music in self.musiclist:
            self.music_dict[music] = 0

        def pipline(url):
            """parcours le fichier ligne par ligne"""
            with open(url, "r") as f:
                for ligne in f:
                    yield ligne

        def nombres():
            """retoune une liste des totaux en ordre """
            n_j = []
            for i in range(len(self.musiclist)):
                n = [1 for ligne in pipline("last_sound.txt") if self.nom_son(self.musiclist[i]) in ligne]
                n = sum(n)
                n_j.append(n)
            return n_j

        def music_pef(liste:list):
            """Affiche la musique préférée et moins lue"""
            pref = max(liste)
            moins_lue = min(liste)
            indice_moins_lu = liste.index(moins_lue)
            indice_pref = liste.index(pref)
            print(f"La musique préfétée est : {self.nom_son(self.musiclist[indice_pref])}")
            print(f"La musique la moins est : {self.nom_son(self.musiclist[indice_moins_lu])}")


        listes_totaux = nombres()

        # départager les valeur de la liste qui sont dans le dictionnaire
        for i, total in enumerate(listes_totaux):
            self.music_dict[self.musiclist[i]] = total

        for url, n_ in self.music_dict.items():# Affiche de façon formater les musiques
            print(f"musique : {self.nom_son(url)}", f"nombre_joué : {n_}", sep="\t")

        print(f"total_: {sum(listes_totaux)}")# affiche le total des musics enregistrées
        music_pef(listes_totaux)

        self.son.unload()

if __name__ == '__main__':
    LecteurAudioApp().run()