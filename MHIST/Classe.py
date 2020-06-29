"""
:author : Cyril MOINEAU
:creation_date : 12/02/20
:last_change_date : 18/03/20
:description : Définition d'un intervalle_estimer pour les histogrammes MHIST.
"""
from sys import getsizeof


class Classe(object):
    def __init__(self, boundaries, joint_distribution):
        """
        Initialisation d'une classe de l'histogramme MHIST.
        :param boundaries:
        :param joint_distribution:
        """
        self.boundaries = boundaries
        self.joint_distribution = joint_distribution
        self.max_diff, self.max_dim = self.max_aera_diff()
        self.nb_tuple = []
        self.nb_distinct_value = []

    def joint_to_marginal(self, joint):
        """
        Calcul la distribution jointe à partir des distributions marginales.
        :param joint:
        :return:
        """
        nb_dim = len(self.boundaries)
        marginal = []
        # Anciennement, cette boucle était un simple "marginal = [{}] * nb_dim" le problème est qu'en faisant cela,
        # python crée un tableau de pointeur vers un seul dictionnaire d'où des erreures ...
        for i in range(nb_dim):
            marginal.append({})
        for t in joint:  # Boucle sur chaque tuple de la distribution jointe
            for d in range(nb_dim):  # Boucle sur chaque dimension
                if t[0][d] in marginal[d].keys():
                    marginal[d][t[0][d]] += t[1]
                else:
                    marginal[d][t[0][d]] = t[1]
        marginal = [sorted(k.items(), key=lambda x: x[0]) for k in marginal]
        return marginal

    def freq(self, dim, k, marginal_distribution):
        """
        Calcul de la valeur critique "frequence".
        :param dim: dimension à étudier.
        :param k: Index de la valeur distinct.
        :param marginal_distribution: distribution marginale des données.
        :return: Nombre d'apparition dans le jeu de données de la kième valeur distinct de la dim-ième dimension
        """
        return marginal_distribution[dim][k][1]

    def spread(self, dim, k, marginal_distribution):
        """
        Calcul de la valeur critique "écartement".
        :param dim: dimension à étudier.
        :param k: Index de la valeur distinct.
        :param marginal_distribution: distribution marginale des données.
        :return: Différence entre la kième valeur distinct et la k+1ième valeur distinct de la dim-ième dimension
        """
        return marginal_distribution[dim][k + 1][0] - marginal_distribution[dim][k][0]

    def aera(self, dim, k, marginal_distribution):
        """
        Calcul de la valeur critique "surface".
        :param dim: dimension à étudier.
        :param k: Index de la valeur distinct.
        :param marginal_distribution: distribution marginale des données.
        :return: Produit de la fréquence et de l'écartement.
        """
        return self.freq(dim, k, marginal_distribution) * self.spread(dim, k, marginal_distribution)

    def max_aera_diff(self):
        """
        Renvoit la valeur maximal de "surface" ainsi que la dimension où l'on peut la trouver
        :return:
        """
        max_diff = 0
        max_dim = 0
        marginal_distribution = self.joint_to_marginal(self.joint_distribution)

        for nb_dim in range(len(marginal_distribution)):
            for k in range(len(marginal_distribution[nb_dim]) - 3):
                v = max(
                    [abs(self.aera(nb_dim, k, marginal_distribution) - self.aera(nb_dim, k + 1, marginal_distribution)),
                     abs(self.aera(nb_dim, k + 1, marginal_distribution) - self.aera(nb_dim, k + 2,
                                                                                     marginal_distribution))])
                if v > max_diff:
                    max_diff = v
                    max_dim = nb_dim
        return max_diff, max_dim

    def split(self):
        """
        Séparation d'une classe en deux.
        :return: Deux classes. (-1, -1) s'il n'est pas possible de séparer la classe en deux.
        """
        if self.max_diff != 0:
            # Séparation de la distribution jointe =====================================================================
            joint_distribution_1 = []
            joint_distribution_2 = []
            for it in self.joint_distribution:
                new_bound = (self.boundaries[self.max_dim][0] + self.boundaries[self.max_dim][1]) / 2
                if self.boundaries[self.max_dim][0] <= it[0][self.max_dim] < new_bound:
                    joint_distribution_1.append(it)
                if new_bound <= it[0][self.max_dim] <= self.boundaries[self.max_dim][1]:
                    joint_distribution_2.append(it)
            if joint_distribution_1 == [] or joint_distribution_2 == []:
                return -1, -1
            # Séaparation des frontières ===============================================================================
            boundaries_1 = list(self.boundaries)
            boundaries_2 = list(self.boundaries)
            boundaries_1[self.max_dim] = (min([i[0][self.max_dim] for i in joint_distribution_1]),
                                          max([i[0][self.max_dim] for i in joint_distribution_1]))
            boundaries_2[self.max_dim] = (min([i[0][self.max_dim] for i in joint_distribution_2]),
                                          max([i[0][self.max_dim] for i in joint_distribution_2]))

            # Création des deux nouveaux intervalles ===================================================================
            intervalle_1 = Classe(boundaries_1, joint_distribution_1)
            intervalle_2 = Classe(boundaries_2, joint_distribution_2)

            return intervalle_1, intervalle_2
        else:
            return -1, -1

    def freeze(self):
        """
        Enlève de la mémoire la distribution jointe qui à permis l'initialisation.
        :return:
        """
        marginal = self.joint_to_marginal(self.joint_distribution)
        nb_tuples = 0
        nb_distinct_values = []
        for i in marginal[0]:  # On compte le nombre de tuple selon la dim 0
            nb_tuples += i[1]
        for dim in range(len(self.boundaries)):
            distinct_value_in_n = len(marginal[dim])
            nb_distinct_values.append(distinct_value_in_n)
        self.nb_distinct_value = nb_distinct_values
        self.nb_tuple = nb_tuples
        self.joint_distribution = None

    def print(self, dims):
        """
        Affichage de la classe projetté sur les 2 attributs définis dans dims
        :param dims:
        :return:
        """
        return ((self.boundaries[dims[0]][0], self.boundaries[dims[1]][0]),
                self.boundaries[dims[0]][1] - self.boundaries[dims[0]][0],
                self.boundaries[dims[1]][1] - self.boundaries[dims[1]][0])

    def intersection_intervalle(self, intervalle, tab_dimension):
        """
        Fonction permettant de savoir si la classe intersectionne une zone.
        :param intervalle: Liste d'intervalle [min, max] pour chaque attribut, doit correspondre à l'ordre de
        la liste "attribut_a_estimer"
        :param tab_dimension: Liste d'attribut (sous forme de str, doit correspondre aux noms donnés dans
        self.attributes_name)
        :return:
        """
        it = 0
        flag_intersect = True
        while it < len(tab_dimension) and flag_intersect:
            if not self.intersection_une_dimension(intervalle[it], tab_dimension[it]):
                flag_intersect = False
            it += 1
        return flag_intersect

    def intersection_une_dimension(self, intervalle1D, dimension):
        """
        Méthode intermédiaire à la méthode  "intersection_intervalle".
        :param intervalle1D:
        :param dimension:
        :return:
        """
        borne_inf_in = self.boundaries[dimension][0] <= intervalle1D[0] <= self.boundaries[dimension][1]
        borne_sup_in = self.boundaries[dimension][0] <= intervalle1D[1] <= self.boundaries[dimension][1]
        return borne_inf_in or borne_sup_in

    def estimate_card(self, tab_dim, intervalle_a_estimer):
        """
        Réalise un estimation de cardinalité dans une zone.
        :param tab_dim:
        :param intervalle_a_estimer:
        :return:
        """
        card_estim = 0
        # On vérifie si notre intervalle_estimer n'est pas complètement inclus dans la conjonction =====================
        flag_inter_completement_inclus = True
        # TODO : Faire avec une boucle while ...
        for d in range(len(tab_dim)):
            if not (intervalle_a_estimer[d][0] <= self.boundaries[tab_dim[d]][0] and
                    self.boundaries[tab_dim[d]][1] <= intervalle_a_estimer[d][1]):
                flag_inter_completement_inclus = False

        # Test pour ne pas considérer un intervalle_estimer vide ou bien si l'on ne peut pas juste éviter tout calcul ==
        if not flag_inter_completement_inclus:
            # On regarde si l'intervalle_estimer intersectionne l'intervalle à estimer =================================
            if self.intersection_intervalle(intervalle_a_estimer, tab_dim):
                F = 0  # Sommes des fréquences estimées
                D = 1  # Estimation du nombre de valeurs distincts dans l'intervalle_estimer
                D_i = 1  # Estimation du nombre de valeurs distincts dans l'intersection
                for d in range(len(tab_dim)):
                    d_i = 0
                    pas = (self.boundaries[tab_dim[d]][1]-self.boundaries[tab_dim[d]][0])/self.nb_distinct_value[tab_dim[d]]
                    frequence = self.nb_tuple / float(self.nb_distinct_value[tab_dim[d]])
                    for id_value in range(self.nb_distinct_value[tab_dim[d]]):
                        value = self.boundaries[tab_dim[d]][0] + id_value * pas
                        if intervalle_a_estimer[d][0] <= value <= intervalle_a_estimer[d][1]:
                            d_i += 1
                    D *= self.nb_distinct_value[tab_dim[d]]
                    D_i *= d_i
                    F += frequence
                # F / D correspond à la fréquence estimé
                card_estim = (F / D) * D_i
        # Ici on test si on a évité les calculs car l'intervalle_estimer est entièrement inclus dans la conjonction
        else:
            card_estim = self.nb_tuple  # Auquel cas pas besoin d'estimation !
        return card_estim

    def get_size(self):
        """
        Renvoit l'espace de stockage necessaire pour la classe.
        :return:
        """
        res = 0
        res += getsizeof(self.boundaries)
        res += getsizeof(self.nb_tuple)
        res += getsizeof(self.joint_distribution)  # Devrait être 0 ...
        return res
