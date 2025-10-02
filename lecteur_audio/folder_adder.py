"""
folder_adder est le fichier source de l'importation de fichiers par l'ajout de répertoires,
de façon dynamique
"""
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from os.path import exists, abspath, join
from kivy.factory import Factory
from kivy.event import EventDispatcher
from kivy.base import runTouchApp
from os import listdir
from os.path import exists
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from utils import clean

class FilesParser:
    """Gère la verification des fichiers selectionnés et valide les entrées"""
    path = ""
    files = []

    def trier(self):
        for file in listdir(self.path):
            if file.split(".")[-1] in ["mp3", "MP3"]:
                self.files.append(file)


class FolderAdder(FileChooserListView):
    """selecteur de repertoire"""
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.filters = [self.filter_files]

    def filter_files(self, inst, file):
        ext = file.split(".")[-1]
        return  ext in ["mp3", "MP3"]

class FolderChooser(Popup):
    """Popup qui servira pour afficher et manipuler le selecteur de fichiers"""
    filesparser = FilesParser()
    # input à completés dans le fichier principale
    music_list = None
    box = None
    parentfolders = None
    build_sound = None
    menu_ajout = ObjectProperty()
    builder_ui = None
    build_files = None
    scroll = None

    def dismiss(self, *_args, **kwargs):
        self.processing()
        super().dismiss(*_args, **kwargs)

    def processing(self):
        self.filesparser.path = self.ids.file_chooser.path
        if exists(self.filesparser.path):
            self.filesparser.trier()
        else:
            popup = Popup(title="Attention")
            label = Factory.Label(text="Dossier introuvable")
            popup.content = label
            popup.open()

    def react_closefc(self):
        """Enregistrer et Charger les musiques qui se trouves dans le repertoire"""
        file = self.filesparser
        if file.path:
            with open("folders.txt", "r") as f:
                lignes = f.read()
                if file.path in lignes:
                    pass
                else:
                    with open("folders.txt", "a+") as fl:
                        fl.write("\n" + file.path)
            if self.ids.file_chooser.path not in self.parentfolders:
                self.parentfolders.append(file.path)

                # Nettoyer la lister et mettre à jour
                clean(self.box)
                Clock.schedule_once(lambda dt: self.build_files(), 0.1)
                Clock.schedule_once(lambda dt: self.build_sound(), 0.1)

    def on_dismiss(self):
        self.menu_ajout.state = "normal"
        super().on_dismiss()



popup_chooser = Builder.load_file('kv_files/folder_adder.kv')

validate_btn = popup_chooser.ids.validate   # Bouton de validation du selecteur de répertoire
file_chooser = popup_chooser.ids.file_chooser # Selecteur de ficher

if __name__ == '__main__':
    from kivy.app import App
    class TestApp(App):
        def build(self):
            return Builder.load_file(filename="kv_files/folder_adder.kv").open()

    TestApp().run()