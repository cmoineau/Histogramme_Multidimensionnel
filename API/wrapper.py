# -*- coding: UTF-8 -*-
"""
:author : Cyril MOINEAU
:creation_date : 26/06/20
:last_change_date : 01/07/20
:description : Définition d'un wrapper pour interragir les histogrammes sérialisé
"""
from pickle import load
from MHIST import Mhist
from GENHIST import Genhist
from STHOLES import Stholes, Workload
from os import remove
from os.path import exists
from glob import glob

dic_histo = {"mhist": 0, "genhist": 1, "stholes": 2}


class Histogramme_wrapper(object):
    def __init__(self):
        """
        Le wrapper permet d'effectuer des opérations pour créer ou supprimer des histogrammes sérialisé.
        On peut aussi charger un histogramme dans le wrapper afin de réaliser des opérations (estimation, màj, description).
        """
        self.histogramme = None
        self.type_histogramme = None
        self.path = None

    def charger_histogramme(self, path):
        """
        Permet de charger un histogramme sérialisé dans le wrapper
        :param path:
        :return:
        """
        with open(path, "rb") as f:
            try:
                self.histogramme = load(f)
            except Exception as e:
                print(e)
            terminaison = path.split("/")[-1].split(".")[-1]
            self.type_histogramme = dic_histo[terminaison]
            self.path = path

    def creer_MHIST(self, data, attributes_name, nom_histogramme, max_classes=500):
        """
        Permet de créer un histogramme MHIST
        :param data: Liste des donnée (doit correspondre au paramètre attributes_name)
        :param attributes_name: Nom des attributs (doit correspondre au paramètre data)
        :param nom_histogramme: Nom utilisé pour charger l'histogramme
        :param max_classes: Par défaut initialisé avec 500 classes
        :return: True si l'opération c'est bien déroulé, False sinon
        """
        try:
            histo = Mhist.Mhist(data, attributes_name, max_classes)
            histo.save("./saved_hist/" + nom_histogramme + ".mhist")
        except Exception as e:
            print(e)
            return False
        return True

    def creer_GENHIST(self, data, attributes_name, nom_histogramme, b=50, xi=10):
        """
        Permet de créer un histogramme GENHIST
        :param data: Liste des donnée (doit correspondre au paramètre attributes_name)
        :param attributes_name: Nom des attributs (doit correspondre au paramètre data)
        :param nom_histogramme: Nom utilisé pour charger l'histogramme
        :param b: Nombre de classe de plus grande densité selectionné à partir de la partition régulière
        :param xi: Nombre de classe de la partition régulière, qui est égale à xi**nombre_de_dimension
        :return: True si l'opération c'est bien déroulé, False sinon
        """
        try:
            alpha = (1 / 2) ** (1 / len(data))
            histo = Genhist.Genhist(data, attributes_name, b, xi, alpha)
            histo.save("./saved_hist/" + nom_histogramme + ".genhist")
        except Exception as e:
            print(e)
            return False
        return True

    def creer_STHoles(self, attributes_name, nom_histogramme, max_classes=500):
        """
        :param attributes_name: Nom des attributs (doit correspondre au paramètre data)
        :param nom_histogramme: Nom utilisé pour charger l'histogramme
        :param max_classes: Par défaut initialisé avec 500 classes
        :return:
        """
        try:
            histo = Stholes.Stholes(attributes_name, max_classes)
            histo.save("./saved_hist/" + nom_histogramme + ".stholes")
        except Exception as e:
            print(e)
            return False
        return True

    def estimer(self, attributs, zones):
        """
        Réalise une estimation de la cardinalité
        :param attributs: Attributs sur lesquels on veut réaliser l'estimation (doit correspondre au paramètre zones)
        :param zones: Liste d'intervalles sur chaque attribut de la zone à estimer (doit correspondre au paramètre attributs)
        :return:
        """
        if self.histogramme is None:
            raise ValueError("Il faut d'abord charger un histogramme !")
        return self.histogramme.estimer(attributs, zones)

    def train_STHoles(self, data, nb_queries, volume=0.01):
        """
        Réalise une mise à jour de l'histogramme STHoles avec des requêtes aléatoires
        :param data: Jeu de donnée à utiliser
        :param nb_queries: Nombre de requêtes à créer
        :param volume: Paramètre optionnel définis le volume des requêtes généré alétoirement /!\ À prioris pas besoin
        de modifier ce paramètre /!\
        :return:
        """
        if self.type_histogramme is None or self.type_histogramme != 2:
            raise ValueError("Il faut charger un histogramme STHoles pour l'entraîner !")
        workload = Workload.create_workload_full(data, volume, nb_queries)
        self.histogramme.BuildAndRefine(workload)
        self.histogramme.save(self.path)

    def show_hist(self):
        """
        Affiche les histogrammes.
        /!\ Disponible que si l'on utilise le wrapper directement /!\
        Pour créer l'API j'ai du enlever les dépendances à matplotlib, cette méthode ne fonctionne donc plus.
        Pour la refaire fonctionner, il faut aller dans les dossier des histogrammes et retirer les commentaires au
        niveau de l'importation de matplotlib.
        :return:
        """
        if self.histogramme is None:
            raise ValueError("Il faut d'abord charger un histogramme !")
        self.histogramme.print()

    def remove_hist(self, path):
        """
        Supprime un histogramme
        :param path:
        :return:
        """
        if exists(path):
            if path.split('.')[-1] in ['mhist', 'genhist', 'stholes']:
                remove(path)
                return True
        return False

    def list_hist(self):
        """
        Renvoit une liste des histogrammes sérialisés
        :return:
        """
        res = []
        res += (glob("./saved_hist/*.mhist"))
        res += (glob("./saved_hist/*.genhist"))
        res += (glob("./saved_hist/*.stholes"))
        return res

    def get_attributes(self):
        if self.histogramme is None:
            print("Il faut d'abord charger un histogramme !")
            return None
        return self.histogramme.attributes_name