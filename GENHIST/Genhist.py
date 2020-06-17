"""
:author : Cyril MOINEAU
:creation_date : 21/02/20
:last_change_date : 07/04/20
:description : Définition d'un histogramme GENHIST.
"""
from GENHIST import Intervalle as intervalle
import random
from matplotlib import patches
import matplotlib.pyplot as plt
from sys import getsizeof
import numpy as np
from utils import est_inclus, epsilon
from pickle import dump


class Genhist(object):
    def __init__(self, data_set, dim_name, b, xi, alpha, verbeux=False):
        """
        Initialisation d'un histogramme genhist
        :param data_set: list /!\ Cette variable va subir des modifications, on en fait une copie au début du script /!\
        :param dim_name: list liste des noms des attributs pour pouvoir faire les estimations
        :param b:
        :param xi: Fixe le nombre d'intervalle obtenue lors des partitionnements (intervalle temporaire permettant la
        création de l'histogramme. Si xi trop grand (ie: xi^nb_dim), alors on risque de faire exploser la complexité.
        :param alpha: Variable influant sur l'évolution de xi, recommandé d'initialiser à (1/2)^(1/nb_dim)
        :param verbeux: boolean : Optionnel, affiche la progression de construction de l'histogramme.
        """
        # On fait une copie du jeu de données car nous aurons besoin de le maniuler dans la suite
        # Note: deepcopy ne fonctionne pas à cause d'une erreur de récursion
        data_set = np.array(data_set).copy()
        data_set = [list(d) for d in data_set]

        self.verbeux = verbeux
        self.n = len(data_set[0])  # On définit le nombre de tuple
        self.dim_name = dim_name
        self.tab_intervalle = []
        self.tot_nb_point_remove = 0

        construction_in_progress = True
        while construction_in_progress:
            partition = self.partitionning(data_set, xi)
            # On prends les b plus grandes densité
            partition = sorted(partition, reverse=True, key=lambda x: x.densite)[:b]
            for inter in partition:
                moyenne = 0  # Calcul de la densité moyenne des voisins
                for v in inter.voisin:
                    moyenne += v.densite
                moyenne = moyenne / len(inter.voisin)
                if inter.densite > moyenne:
                    data_set = self.supprimer_elts(inter, moyenne, data_set)
                    inter.densite = (inter.densite - moyenne)
                    self.tab_intervalle.append(inter.copy())

            tmp = (len(data_set[0]) / (len(data_set[0]) + self.tot_nb_point_remove)) ** (1/len(data_set))
            xi = int(min(tmp, alpha) * xi)  # On veut la partie entière du nombre
            if len(data_set[0]) == 0:
                construction_in_progress = False
            elif xi <= 1:
                self.tab_intervalle.append(
                    intervalle.Intervalle([(min(data_set[d]), max(data_set[d])) for d in range(len(data_set))]
                                          , densite=len(data_set[0])/self.n))
                construction_in_progress = False

    def supprimer_elts(self, inter, densite_moyenne, data_set):
        """
        Enlève des points de manière aléatoire de data_set et renvoit le data_set modifié.
        nb_point_to_remove = round((inter.densite - densite_moyenne) * self.n)
        :param inter:
        :param densite_moyenne:
        :param data_set:
        :return:
        """
        nb_point_to_remove = round((inter.densite - densite_moyenne) * self.n)
        self.tot_nb_point_remove += nb_point_to_remove
        cpt = len(data_set[0]) - 1
        nb_pt_rm = 0
        while nb_pt_rm != nb_point_to_remove:  # Parcour inverse du tableau pour éviter les problèmes d'index
            if cpt == -1:
                cpt = len(data_set[0]) - 1
            if random.random() > 0.5:  # TODO : Faire une suppression plus intelligente ?
                for d in range(len(data_set)):
                    del data_set[d][cpt]
                nb_pt_rm += 1
            cpt -= 1
        return data_set

    def partitionning(self, data, xi):
        '''
        Cette fonction renvoit (xi ** d) intervalles de largeur égale. Où d = nb de dimension de data.
        :param data:
        :param xi:
        :return:
        '''
        if self.verbeux:
            print('Création d\'une nouvelle partition de ', xi ** len(data), ' intervalles')
        tab_intervalle = []
        tab_min_max = [(min(i), max(i)) for i in data]
        tab_pas = [(i[1] - i[0]) / xi for i in tab_min_max]
        tab_avancement = [i[0] for i in tab_min_max]
        nb_dim = len(tab_min_max)
        terminaison = False  # Boolean pour simuler une boucle do-while
        while not terminaison:
            new_boundary = [[tab_avancement[i], tab_avancement[i] + tab_pas[i]] for i in range(nb_dim)]
            tab_intervalle.append(intervalle.Intervalle(new_boundary))
            dim = 0
            maj_pas = True
            while maj_pas:
                if dim == nb_dim:  # On a atteint la fin
                    maj_pas = False
                    terminaison = True
                else:
                    # Si avancer nous fait dépasser alors, on revient à 0 pour cette dimension et on incrémente la dimension
                    if tab_avancement[dim] + (2 * tab_pas[dim]) > tab_min_max[dim][1] + epsilon:
                        tab_avancement[dim] = tab_min_max[dim][0]  # On reset l'avancement de cette dimension
                        dim += 1
                    # Si on peut avancer alors on avance et on arrête notre mise à jour
                    else:
                        tab_avancement[dim] = tab_avancement[dim] + tab_pas[dim]
                        maj_pas = False

        # Mis à jour des voisins =======================================================================================
        '''
        Précédemment, j'ai crée un tableau d'intervalle de tel sorte à ce qu'il ressemble à ceci :
                a b c
                d e f   => [a, b, c, d, e, f, g, h, i]
                g h i
        On à aplatit la "matrice de partitionnement", on va donc travailler avec des modulos pour trouver les voisins.
        '''
        for i in range(len(tab_intervalle)):
            # Selon chaque dimension, un intervalle possède au mieux deux voisins
            for dim in range(nb_dim):
                # Test pour savoir si on est tout à droite
                if (i + 1) % (xi ** (dim + 1)) == 1 and i + xi ** dim in range(len(tab_intervalle)):
                    tab_intervalle[i].voisin.append(tab_intervalle[i + xi ** dim])
                # Test pour savoir si on est tout à gauche
                elif (i + 1) % (xi ** (dim + 1)) == 0 and i - xi ** dim in range(len(tab_intervalle)):
                    tab_intervalle[i].voisin.append(tab_intervalle[i - xi ** dim])
                else:
                    if i - (xi ** dim) in range(len(tab_intervalle)):
                        tab_intervalle[i].voisin.append(tab_intervalle[i - xi ** dim])
                    if i + (xi ** dim) in range(len(tab_intervalle)):
                        tab_intervalle[i].voisin.append(tab_intervalle[i + xi ** dim])

        # Mise à jour de la densité ====================================================================================
        for i in range(len(data[0])):
            point = [d[i] for d in data]
            if self.verbeux:
                print('Mise à jour de la densité :', i, '/', len(data[0]))
            # TODO : Ici on parcourt linéairement nos intervalles partitionné, or justement ils partitionnent l'espace,
            #  on devrait utiliser cette propriétés pour trouver plus rapidement à quelle boundary appartient le point.
            maj_pas = True
            cpt_intervalle = 0
            while maj_pas:
                if est_inclus(point, tab_intervalle[cpt_intervalle].boundary):
                    tab_intervalle[cpt_intervalle].densite += 1
                    maj_pas = False
                cpt_intervalle += 1
        for inter in tab_intervalle:
            inter.densite = inter.densite / self.n
        return tab_intervalle

    def print(self, tab_intervalle=-1):
        """
        Affiche l'histogramme GENHIST
        :param tab_intervalle: Correpond aux dimensions à afficher
        :return:
        """
        if tab_intervalle == -1:
            tab_intervalle = self.tab_intervalle
        figure = plt.figure()
        axes = plt.axes()
        axes.set_xlim(left=-10, right=10)
        axes.set_ylim(bottom=-10, top=10)

        subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
        for i in tab_intervalle:
            bound, w, h = i.print()
            subplot.add_patch(patches.Rectangle(bound, w, h, linewidth=1, fill=False))

    def estimer(self, tab_attribut, boundary):
        card = 0
        for intervalle in self.tab_intervalle:
            card += intervalle.estimate_card([self.dim_name.index(att) for att in tab_attribut], boundary) * self.n
        if card < 0:
            raise ValueError('Cardinalité négative ...')
        return card

    def get_size(self):
        size = 0
        for intervalle in self.tab_intervalle:
            size += intervalle.get_size()
        size += getsizeof(self.dim_name)
        return size

    def save(self, path):
        f = open(path, 'wb')
        dump(self, f)
        f.close()
