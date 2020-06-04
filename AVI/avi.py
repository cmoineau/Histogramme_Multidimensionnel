"""
:author : Cyril MOINEAU
:creation_date : 20/02/20
:last_change_date : 20/02/20
:description : Estimation en utilisant l'hypothèse indépendance des variables entre chaque attributs.
"""
import numpy as np
from scipy.stats.mstats import mquantiles


class Avi(object):
    def __init__(self, data, attributs):
        nb_intervalle = 100
        self.nb_tuple = len(data[0])
        self.frequence = self.nb_tuple / nb_intervalle
        self.nb_dim = len(data)
        self.attributs = attributs
        self.intervalles = [mquantiles(d, [i/nb_intervalle for i in range(100)]) for d in data]

    def estimation(self, tab_dim, intervalles_estimer):
        '''
        Estimation en utilisant l'hypothèse d'indépendance des attributs
        :param tab_dim: A tab of the id attributes of which we want to estimate the cardinality.
        :param intervalle_estimer: The intervalle we want to estimate
        :return: The number of element in the multi-dim interval.
        '''
        nb_tuple = []
        for dim in tab_dim:
            index_dim = self.attributs.index(dim)
            intervalle = self.intervalles[index_dim]
            nb_ds_dim = 0
            recherche_premier_pivot = True
            recherche_deuxieme_pivot = True
            intervalle_estimer = intervalles_estimer[index_dim]
            for i in range(len(intervalle)):  # TODO : Boucle while pour optimisation ?
                borne = intervalle[i]
                if recherche_premier_pivot:
                    if borne > intervalle_estimer[0]:
                        if borne > intervalle_estimer[1]:  # Es-ce que le deuxième pivot dépasse la borne ?
                            # si non
                            if i != 0:  # On test si on était à la première borne
                                # Si non alors on à trouvé les deux pivots
                                nb_ds_dim += ((intervalle_estimer[1] - intervalle_estimer[0]) / (borne - intervalle[i-1])) * self.frequence
                                recherche_deuxieme_pivot = False
                            else:
                                # Si on était à la première borne, on est en dehors de la zone des données, on revoit 0
                                return 0
                        else:
                            # Le deuxième pivot est plus loins que la brone courante
                            if i != 0:
                                # Si on n'est pas à la première borne
                                nb_ds_dim += ((borne - intervalle_estimer[0]) / (borne - intervalle[i - 1])) * self.frequence
                            # Dans le cas else, on ne fait rien.
                        recherche_premier_pivot = False
                elif recherche_deuxieme_pivot:
                    if borne > intervalle_estimer[1]:
                        nb_ds_dim += ((intervalle_estimer[1] - intervalle[i - 1]) / (borne - intervalle[i - 1])) * self.frequence
                        recherche_deuxieme_pivot = False
                    else:
                        nb_ds_dim += self.frequence
            nb_tuple.append(nb_ds_dim)
        res = 1
        for n in nb_tuple:
            res *= n
        res *= (1/self.nb_tuple) ** (len(tab_dim)-1)
        return res
