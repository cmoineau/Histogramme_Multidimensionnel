"""
:author : Cyril MOINEAU
:creation_date : 20/02/20
:last_change_date : 20/02/20
:description : Estimation en utilisant l'hypothèse indépendance des variables entre chaque attributs.
"""

from collections import Counter
import numpy as np


class Avi(object):
    def __init__(self, data):
        self.nb_tuple = len(data[0])
        self.nb_dim = len(data)
        self.tab_count = [Counter(attribut) for attribut in data]  # On compte le nombre d'apparition de chaque élément
        self.tab_count = [sorted(k.items(), key=lambda x: x[0]) for k in self.tab_count]  # On le stock dans un tableau

    def estimation(self, tab_dim, intervalle_estimer):
        '''
        Estimation en utilisant l'hypothèse d'indépendance des attributs
        :param tab_dim: A tab of the id attributes of which we want to estimate the cardinality.
        :param intervalle_estimer: The interval we want to estimate
        :return: The number of element in the multi-dim interval.
        '''

        # On calcule la distribution marginale selon chaque dimension de l'intervalle_estimer a estimer ================
        marginal_distribution = []
        for i in range(len(tab_dim)):
            marginal_distribution.append([])
            for valeur_distinct in self.tab_count[tab_dim[i]]:
                if intervalle_estimer[i][0] <= valeur_distinct[0] <= intervalle_estimer[i][1]:
                    marginal_distribution[i].append(valeur_distinct[1])

        #  On construit le tab_estim en projettant à chaque fois sur une nouvelle dim, pour augmenter sa dimension =====
        tab_estim = np.array(marginal_distribution[0])  # On commence sur la première dimension

        for i in range(len(marginal_distribution) - 1):
            # Pour chaque nouvelle dimension, on fait le produit matriciel de tab_estim actuelle et de la distribution
            # marginale de la nouvelle dimension
            tab_estim = np.array([(tab_estim * e / self.nb_tuple) for e in marginal_distribution[i + 1]])
        res = float(tab_estim.sum())
        tab_estim = None
        marginal_distribution = None
        # Après avoir crée le tableau des cardinalités estimé, on sommes les cardinalités de toutes les dimensions =====
        return res
