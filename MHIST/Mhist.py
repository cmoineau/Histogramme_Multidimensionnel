"""
:author : Cyril MOINEAU
:creation_date : 12/02/20
:last_change_date : 18/02/20
:description : Définition d'un histogramme MHIST.
"""
from matplotlib import patches
import matplotlib.pyplot as plt
from MHIST import Classe
from collections import Counter
from sys import getsizeof
from pickle import dump


class Mhist(object):
    def __init__(self, data, attributes_name, nb_max_intervalle, verbeux=False):
        """
        Initialisation d'un histogramme
        :param data: list[list] Les données que doit estimer l'histogramme.
        :param attributes_name: list[string] Noms donné aux attributs. Utile pour l'estimation.
        :param nb_max_intervalle: int: Définis le nombre maximum d'intervalle.
        :param verbeux: boolean: permet l'affichage de certain print.
        """
        # On test les entrées ==========================================================================================
        nb_dim = len(data)
        nb_tuple = len(data[0])
        for d in range(nb_dim):
            if len(data[d]) != nb_tuple:
                raise ValueError('ERREUR : Tous les attributs doivent posséder le même nombre d\'élement !')
        if nb_dim != len(attributes_name):
            raise ValueError('ERREUR : Vous devez nommer tous les attributs !')

        # Pour l'affichage
        self.min_max = [(min(a), max(a)) for a in data]

        # Création de la distribution jointe ===========================================================================
        tableau_de_coordonee = []
        for i in range(nb_tuple):
            coordonnee = []
            for j in range(nb_dim):
                coordonnee.append(data[j][i])
            tableau_de_coordonee.append(tuple(coordonnee))
        joint_distribution = Counter(tableau_de_coordonee)
        joint_distribution = sorted(joint_distribution.items(), key=lambda t: t[0])

        # Initialisation des attributs =================================================================================
        # Création du premier intervalle
        fi = Classe.Classe([(min(data[j]), max(data[j])) for j in range(nb_dim)], joint_distribution)
        self.verbeux = verbeux
        self.tab_classe = []
        self.tab_classe.append(fi)
        self.nb_max_intervalle = nb_max_intervalle
        self.attributes_name = attributes_name
        # On lance l'algorithme qui va séparer successivement le premier intervalle
        self.build()

    def trouver_intervalle_critique(self):
        """
        Renvoit l'index de l'intervalle qui a le plus besoin d'être partitionné.
        :return: int: index
        """
        max_diff = 0
        max_intervalle = 0
        for intervalle_id in range(len(self.tab_classe)):
            if self.tab_classe[intervalle_id].max_diff > max_diff:
                max_intervalle = intervalle_id
                max_diff = self.tab_classe[intervalle_id].max_diff
        return max_intervalle

    def build(self):
        """
        Fonction qui va séparer successivement le premier intervalle selon les dimensions critiques.
        :return: None
        """
        impossible_de_split = False
        while len(self.tab_classe) < self.nb_max_intervalle and not impossible_de_split:
            if self.verbeux:
                print('Avancement de la construction : ' + str(len(self.tab_classe)) + '/' + str(self.nb_max_intervalle))
            index_intervalle_crit = self.trouver_intervalle_critique()
            it1, it2 = self.tab_classe[index_intervalle_crit].split()
            if (it1, it2) != (-1, -1):
                # On retire l'ancien intervalle et on le remplace par les deux nouveaux.
                del self.tab_classe[index_intervalle_crit]
                self.tab_classe.append(it1)
                self.tab_classe.append(it2)
            else:
                # On arrive ici si l'on dépasse le nombre de valeur distinct avec le nombre d'intervalle
                impossible_de_split = True
        for it in self.tab_classe:
            # Une fois que l'on à terminé, je supprime les distributions marginale des intervalles.
            it.freeze()

    def print(self):
        """
        Affiche l'histogramme multidimensionnel en le projettant sur les deux premiers attributs.
        :return:
        """
        dim_names = self.attributes_name[:2]
        figure = plt.figure()
        axes = plt.axes()
        min_1 = self.min_max[0][0]
        min_2 = self.min_max[1][0]

        max_1 = self.min_max[0][1]
        max_2 = self.min_max[1][1]

        axes.set_xlim(left=min_1, right=max_1)
        axes.set_ylim(bottom=min_2, top=max_2)
        axes.set_xlabel(dim_names[0])
        axes.set_ylabel(dim_names[1])
        subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
        for i in self.tab_classe:
            bound, w, h = i.print([self.attributes_name.index(dim_names[0]), self.attributes_name.index(dim_names[1])])
            subplot.add_patch(patches.Rectangle(bound, w, h, linewidth=1, fill=False))
        plt.show()

    def estimer(self, attributs_a_estimer, intervalle_a_estimer):
        """
        Réalise un estimation de cardinalité dans une zone.
        :param attributs_a_estimer: Liste d'attribut (sous forme de str, doit correspondre aux noms donnés dans
        self.attributes_name)
        :param intervalle_a_estimer: Liste d'intervalle [min, max] pour chaque attribut, doit correspondre à l'ordre de
        la liste "attribut_a_estimer"
        :return: cardinalité (float)
        """
        card = 0
        for intervalle in self.tab_classe:
            card += intervalle.estimate_card([self.attributes_name.index(att) for att in attributs_a_estimer],
                                             intervalle_a_estimer)
        return card

    def get_size(self):
        """
        Renvoit l'espace de stockage necessaire pour l'histogramme.
        :return:
        """
        size = 0
        size += getsizeof(self.nb_max_intervalle)
        for intervalle in self.tab_classe:
            size += intervalle.get_size()
        size += getsizeof(self.attributes_name)
        return size

    def save(self, path):
        """
        Sérialise l'objet histogramme en utilisant la librairie pickle.
        :param path:
        :return:
        """
        f = open(path, 'wb')
        dump(self, f)
        f.close()
