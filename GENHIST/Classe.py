"""
:author : Cyril MOINEAU
:creation_date : 24/02/20
:last_change_date : 03/04/20
:description : Définition d'un intervalle pour l'histogramme GENHIST.
"""
from sys import getsizeof
from copy import deepcopy


class Classe(object):
    def __init__(self, intervalle, densite=0):
        self.boundary = intervalle
        self.densite = densite
        self.voisin = []

    def copy(self):
        """
        Renvoit une copie de l'intervalle
        :return:
        """
        return Classe(deepcopy(self.boundary), densite=self.densite)

    def print(self):
        """
        Renvoit les coordonnée pour afficher les intervalles.
        À utiliser avec la fonction print de genhist
        :return:
        """
        return ((self.boundary[0][0], self.boundary[1][0]),
                self.boundary[0][1] - self.boundary[0][0],
                self.boundary[1][1] - self.boundary[1][0])

    def intersection_intervalle(self, intervalle, tab_dimension):
        """
        Méthode pour savoir si l'intervalle intersectionne l'intervalle
        :param intervalle: Classe sous forme [(x1, y1), ... ,(xn, yn)]
        :param tab_dimension:
        :return:
        """
        it = 0
        flag_intersect = True
        while it < len(tab_dimension) and flag_intersect:
            if not self.intersection_une_dimension(intervalle, tab_dimension[it]):
                flag_intersect = False
            it += 1
        return flag_intersect

    def intersection_une_dimension(self, intervalle, dimension):
        borne_inf_in = self.boundary[dimension][0] <= intervalle[dimension][0] <= self.boundary[dimension][1]
        borne_sup_in = self.boundary[dimension][0] <= intervalle[dimension][1] <= self.boundary[dimension][1]
        return borne_inf_in or borne_sup_in

    def estimate_card(self, tab_dim, intervalle_a_estimer):
        surface_commune = 1
        for d in range(len(tab_dim)):
            if intervalle_a_estimer[d][0] < self.boundary[tab_dim[d]][0]:
                if intervalle_a_estimer[d][1] < self.boundary[tab_dim[d]][0]:
                    return 0
                elif intervalle_a_estimer[d][1] < self.boundary[tab_dim[d]][1]:
                    surface_commune *= (intervalle_a_estimer[d][1] - self.boundary[tab_dim[d]][0])
                else:
                    surface_commune *= (self.boundary[tab_dim[d]][1] - self.boundary[tab_dim[d]][0])
            else:
                if intervalle_a_estimer[d][0] >= self.boundary[tab_dim[d]][1]:
                    return 0
                elif intervalle_a_estimer[d][1] < self.boundary[tab_dim[d]][1]:
                    surface_commune *= (intervalle_a_estimer[d][1] - intervalle_a_estimer[d][0])
                elif intervalle_a_estimer[d][1] > self.boundary[tab_dim[d]][1]:
                    surface_commune *= (self.boundary[tab_dim[d]][1] - intervalle_a_estimer[d][0])
        return (surface_commune/self.surface(tab_dim=tab_dim)) * self.densite

    def surface(self, tab_dim=None):
        res = 1
        if tab_dim is None:
            for i, j in self.boundary:
                res *= (j - i)
        else:
            for d in tab_dim:
                res *= (self.boundary[d][1] - self.boundary[d][0])
        return res

    def get_size(self):
        size = 0
        size += getsizeof(self.boundary)
        size += getsizeof(self.densite)
        size += getsizeof(self.voisin)
        return size
