"""
:author : Cyril MOINEAU
:creation_date : 12/02/20
:last_change_date : 18/02/20
:description : Définition d'un histogramme MHIST.
"""
from matplotlib import patches
import matplotlib.pyplot as plt
import MHIST.Intervalle as Intervalle
from collections import Counter
from sys import getsizeof
from pickle import dump


class Mhist(object):
    def __init__(self, data, dim_name,  nb_max_intervalle, verbeux=False):
        """
        Initialisation d'un histogramme
        :param data: list[list] Les données que doit estimer l'histogramme.
        :param dim_name: list[string] Noms donné aux attributs. Utile pour l'estimation.
        :param nb_max_intervalle: int: Définis le nombre maximum d'intervalle.
        :param verbeux: boolean: permet l'affichage de certain print.
        """
        # On test les entrées ==========================================================================================
        nb_dim = len(data)
        nb_tuple = len(data[0])
        for d in range(nb_dim):
            if len(data[d]) != nb_tuple:
                raise ValueError('ERREUR : Tous les attributs doivent posséder le même nombre d\'élement !')
        if nb_dim != len(dim_name):
            raise ValueError('ERREUR : Vous devez nommer tous les attributs !')

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
        # Création du premier boundary
        fi = Intervalle.Intervalle([(min(data[j]), max(data[j])) for j in range(nb_dim)], joint_distribution)
        self.verbeux = verbeux
        self.tab_intervalle = []
        self.tab_intervalle.append(fi)
        self.nb_max_intervalle = nb_max_intervalle
        self.dim_name = dim_name
        # On lance l'algorithme qui va séparer successivement le premier boundary
        self.build()

    def trouver_intervalle_critique(self):
        """
        Renvoit l'index de l'boundary qui a le plus besoin d'être partitionné.
        :return: int: index
        """
        max_diff = 0
        max_intervalle = 0
        for intervalle_id in range(len(self.tab_intervalle)):
            if self.tab_intervalle[intervalle_id].max_diff > max_diff:
                max_intervalle = intervalle_id
                max_diff = self.tab_intervalle[intervalle_id].max_diff
        return max_intervalle

    def build(self):
        """
        Fonction qui va séparer successivement le premier boundary selon les dimensions critiques.
        :return: None
        """
        impossible_de_split = False
        while len(self.tab_intervalle) < self.nb_max_intervalle and not impossible_de_split:
            if self.verbeux:
                print('Avancement de la construction : '+str(len(self.tab_intervalle))+'/'+str(self.nb_max_intervalle))
            index_intervalle_crit = self.trouver_intervalle_critique()
            it1, it2 = self.tab_intervalle[index_intervalle_crit].split()
            if (it1, it2) != (-1, -1):
                # On retire le vieille boundary et on le remplace par les deux nouveaux.
                del self.tab_intervalle[index_intervalle_crit]
                self.tab_intervalle.append(it1)
                self.tab_intervalle.append(it2)
            else:
                # On arrive ici si l'on dépasse le nombre de valeur distinct avec le nombre d'boundary
                impossible_de_split = True
        for it in self.tab_intervalle:
            # Une fois que l'on à terminé, je supprime les distributions marginale des intervalles.
            it.freeze()

    def print(self, dim_names):
        if len(dim_names) != 2:
            raise ValueError('ERREUR : Vous devez envoyer une liste de taille 2 !')
        else:
            figure = plt.figure()
            axes = plt.axes()
            axes.set_xlim(left=-10, right=10)
            axes.set_ylim(bottom=-10, top=10)
            axes.set_xlabel(dim_names[0])
            axes.set_ylabel(dim_names[1])
            subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
            for i in self.tab_intervalle:
                bound, w, h = i.print([self.dim_name.index(dim_names[0]), self.dim_name.index(dim_names[1])])
                subplot.add_patch(patches.Rectangle(bound, w, h, linewidth=1, fill=False))

    def estimate(self, attributs_a_estimer, intervalle_a_estimer):
        card = 0
        for intervalle in self.tab_intervalle:
            card += intervalle.estimate_card([self.dim_name.index(att) for att in attributs_a_estimer],
                                             intervalle_a_estimer)
        return card

    def get_size(self):
        size = 0
        size += getsizeof(self.nb_max_intervalle)
        for intervalle in self.tab_intervalle:
            size += intervalle.get_size()
        size += getsizeof(self.dim_name)
        return size

    def save(self, path):
        f = open(path + '.histo', 'wb')
        dump(self, f)
        f.close()
