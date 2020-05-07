"""
:author : Cyril MOINEAU
:creation_date : 02/03/20
:last_change_date : 23/04/20
:description : Définition d'un histogramme ST-Holes.

Définitions :
    - requête : [ [coordonnée du centre], [longueurs], nombre de tuple renvoyé par la requête ]
    - boundary : (frontière) : [ [frontière d'un intervalle] for dim in nb_dim ]

"""

from sys import getsizeof
import time
from copy import deepcopy, copy
from utils import epsilon
from pickle import dump
import matplotlib.pyplot as plt
from matplotlib import patches
from random import random


class Stholes(object):
    def __init__(self, dim_name, nb_max_bucket, verbeux=False):
        """
        Un histogramme ST-Holes est un histogramme qui peut se définir comme un arbre. Un boundary correspond à un
        histogramme St-Holes. On retrouve des notions tel que celle d'boundary (i.e: noeud) fils ou père.
        Cet histogramme est particulier car il se construit sans regarder les données.
        Ce constructeur produit un histogramme vide, il conviendra d'utiliser la fonction 'BuildAndRefine' et
        'build_and_refine' pour le mettre à jour.
        :param dim_name:
        :param nb_max_bucket:
        :param verbeux:
        """
        self.nb_tuple = 0
        self.children = []
        self.bound = []
        self.nb_max_bucket = nb_max_bucket
        self.dim_name = dim_name
        self.father = None
        self.howasicreated = None
        self.verbeux = verbeux

    def BuildAndRefine(self, workload):
        """
        BuildAndRefine est la fonction à appeler pour mettre à jour un histogramme avec un ensemble de requête.
        :param workload: ensemble de requête : une requête est une liste :
        :return:
        """
        cpt_nb_req = 0
        for requete in workload:
            if self.verbeux:
                print('Traitement de la requête ', cpt_nb_req, '/', len(workload))
            cpt_nb_req += 1
            self.expand_root(requete)
            tab = self.nb_tuple_intervalles(requete)
            for intervalle in tab:
                intervalle[0].shrink_and_drill(requete[0], intervalle[1])
            # Suppression des intervalles excedentaire =================================================================
            while self.count_nb_bucket() > self.nb_max_bucket:
                if self.verbeux:
                    print('Suppression ... encore ', self.count_nb_bucket() - self.nb_max_bucket, ' buckets')
                self.supprimer_intervalle()
        if self.verbeux:
            print('Fin de la mise à jour !')

    def supprimer_intervalle(self):
        low_p, intervalle_rm, changing_intervalle, nouvelle_intervalle, t, nb_tuple_to_remove = self.find_low_penalty()
        # L'intervalle résultant de la fusion annonce le changement de père au fils
        for child in nouvelle_intervalle.children:
            child.father = nouvelle_intervalle

        if nouvelle_intervalle.father is None:
            self.nb_tuple = nouvelle_intervalle.nb_tuple
            self.children = nouvelle_intervalle.children
            for child in nouvelle_intervalle.children:
                child.father = self
            self.bound = nouvelle_intervalle.bound
            self.howasicreated = t
            nouvelle_intervalle = None  # Pour s'assurer qu'on le détruise
        else:
            # Utilisation d'un set pour ne pas avoir deux fois le même boundary à rm
            intervalle_rm = set(intervalle_rm)
            for r in intervalle_rm:
                changing_intervalle.children.remove(r)
            if nb_tuple_to_remove is not None:
                changing_intervalle.nb_tuple -= nb_tuple_to_remove
            changing_intervalle.children.append(nouvelle_intervalle)
            nouvelle_intervalle.howasicreated = t

    def nb_tuple_intervalles(self, requete):
        """
        Renvoit un tableau de tuple intervalle, nombre de tuple dans l'intervalle.
        :param requete:
        :return:
        """
        tab_res = []
        if self.v_inter(requete[0]) > epsilon:
            volume_requete = 1
            for dim in range(len(requete[0])):
                volume_requete *= (requete[0][dim][1]-requete[0][dim][0])
            # Il semblerait que lors du calcul des volumes des approximations faisait que x prenait des valeurs de l'ordre
            # de 1.00001
            x = min(self.v_inter(requete[0]) / volume_requete, 1)
            nb_tuple_dans_intervalle = requete[1] * x
            tab_res = [(self, nb_tuple_dans_intervalle)]

        for child in self.children:
            tab_res += child.nb_tuple_intervalles(requete)
        return tab_res

    def shrink_and_drill(self, bound_requete, nb_tuple):
        """
        Cette fonction n'est à appeler qu'après avoir vérifié que l'intervalle possède des élèments de la requête !
        :param
        :return:
        """
        c1, T1 = self.shrink(bound_requete, nb_tuple)
        if self.estimer(c1, self.dim_name) != T1:
            self.drill(c1, T1)

    def merge_pc(self, child):
        """
        :param child:
        :return: Renvoit l'intervalle qu'on obtiendrait en fusionnant un père (self) avec l'un de ses fils. Ainsi que la
        pénalité associée à cette fusion.
        """
        # Creation du nouvel intervalle ================================================================================
        n_b = Stholes(self.dim_name, self.nb_max_bucket)
        n_b.nb_tuple = self.nb_tuple + child.nb_tuple
        n_b.father = self.father
        n_b.bound = self.bound
        for c in self.children:
            if c is not child:
                n_b.children.append(c)
        for c in child.children:
            n_b.children.append(c)
        # Calcul de la pénalitée =======================================================================================
        penality = abs(self.nb_tuple - n_b.estimer(self.bound, self.dim_name)) + \
                   abs(self.estimer(child.bound, self.dim_name) - n_b.estimer(child.bound, self.dim_name))
        return n_b, penality

    def merge_ss(self, child1, child2):
        """
        :param child:
        :return: Renvoit l'intervalle qu'on obtiendrait en fusionnant un de fils de self. Ainsi que la pénalité associée
        à cette fusion et une liste d'intervalle appartenant à self qui appartiendrait à l'intervalle obtenu suite à la
        fusion.
        """
        # Création du nouvelle intervalle ==============================================================================
        n_b = Stholes(self.dim_name, self.nb_max_bucket)
        n_b.father = child1.father
        n_b.bound = [[min(child1.bound[dim][0], child2.bound[dim][0]), max(child1.bound[dim][1], child2.bound[dim][1])]
                     for dim in range(len(self.bound))]
        for c in child1.children:
            n_b.children.append(c)
        for c in child2.children:
            n_b.children.append(c)
        # Liste des intervalles à tester ===============================================================================
        a_verifier = copy(self.children)
        a_verifier.remove(child1)
        a_verifier.remove(child2)
        to_rm = [child1, child2]
        cpt = len(a_verifier)-1
        while cpt >= 0:
            child = a_verifier[cpt]
            change_la_taille = False
            if child.est_inclus(n_b.bound):
                to_rm.append(child)
                n_b.children.append(child)
                a_verifier.remove(child)
            elif child.intersect(n_b.bound):
                for dim in range(len(n_b.bound)):
                    if n_b.bound[dim][0] <= child.bound[dim][0] <= n_b.bound[dim][1] <= child.bound[dim][1]:
                        n_b.bound[dim][1] = child.bound[dim][1]
                        change_la_taille = True
                    elif child.bound[dim][0] <= n_b.bound[dim][0] <= child.bound[dim][1] <= n_b.bound[dim][1]:
                        n_b.bound[dim][0] = child.bound[dim][0]
                        change_la_taille = True
                    elif child.bound[dim][0] <= n_b.bound[dim][0] <= n_b.bound[dim][1] <= child.bound[dim][1]:
                        n_b.bound[dim][0] = child.bound[dim][0]
                        n_b.bound[dim][1] = child.bound[dim][1]
                        change_la_taille = True
            if change_la_taille:
                to_rm.append(child)
                n_b.children.append(child)
                a_verifier.remove(child)
                cpt = len(a_verifier)-1
            else:
                cpt -= 1
        # Création de variable :
        # vold correspond au volume qu'occupait vp à la place de vn
        vold = n_b.vBox() - sum([intervalle.vBox() for intervalle in to_rm])
        vn = vold + child1.vBox() + child2.vBox()
        vbp = vold + child2.v() + child1.v()
        if vn == 0:
            raise ValueError("Le résultat de la fusion ss donne un volume nul !")
        v_ratio = vold / vn

        # Calcul du nombre de tuple ====================================================================================
        # Dans ce cas, les fils occupe tout l'espace, il faut fusionner les fils pour faire une fusion père fils plus tard
        if self.v() == 0:
            raise ValueError("Drill à mal fait son travail !")
        else:
            nb_tuple_to_rm_from_p = self.nb_tuple * (vold / self.v())
            n_b.nb_tuple = nb_tuple_to_rm_from_p + child1.nb_tuple + child2.nb_tuple
            # Calcul de la pénalitée ===================================================================================
            p1 = abs(self.nb_tuple * (vold / self.v()) - n_b.nb_tuple * (vold / n_b.v()))
            p2 = abs(child1.nb_tuple - n_b.nb_tuple * (child1.v() / vn))
            p3 = abs(child2.nb_tuple - n_b.nb_tuple * (child2.v() / vn))
            penality = p1 + p2 + p3

        return n_b, penality, to_rm, nb_tuple_to_rm_from_p

    def find_low_penalty(self):
        """
        Méthode à appeler pour trouver la plus petite pénalitée obtenue en réalisant une fusion entre un noeud père/fils
        ou deux noeud fils.
        :return:
        """
        a_effacer = -1
        low_p = None
        nouvelle_intervalle = None
        intervalles_rm = []
        changing_intervalle = None
        nb_tuple_rm = None
        if self.v() < epsilon and self.children != []:  # Si l'intervalle n'a plus de place, on fait une fusion père fils qu'on envoie directement
            n_b, _ = self.merge_pc(self.children[0])
            return 0, [self], self.father, n_b, 0, None
        else:
            for i_child, child in enumerate(self.children):
                # On cherche la meilleur combinaison parent enfant =========================================================
                n_b, p = self.merge_pc(child)
                if low_p is None or low_p > p:
                    low_p = p
                    # Dans le cas de fusion parent_child, on a besoin de juste supprimer la référence du père
                    intervalles_rm = [self]
                    nouvelle_intervalle = n_b
                    # On va supprimer le self de son noeud père et mettre le nouvel inervalle dans le noeud père.
                    # Le noeud changeant est donc le noeud père.
                    changing_intervalle = self.father
                    a_effacer = 0
                    nb_tuple_rm = None
                if len(self.children) > 1 and i_child != (len(self.children) - 1):
                    # On cherche les meilleurs combinaisons de fusion enfant enfant ========================================
                    for i_child1 in range(i_child + 1, len(self.children)):
                        n_b, p, to_rm, nb_tuple_to_remove = self.merge_ss(child, self.children[i_child1])
                        if low_p is None:
                            low_p = p
                        if low_p >= p:
                            low_p = p
                            intervalles_rm = to_rm
                            changing_intervalle = self
                            nouvelle_intervalle = n_b
                            a_effacer = 1
                            nb_tuple_rm = nb_tuple_to_remove
                # On regarde récursivement pour chaque enfant ==============================================================
                p, n_intervalle_rm, n_changing_intervalle, n_nouvelle_intervalle, t, nb_tuple_to_remove = child.find_low_penalty()
                if p is not None:
                    if low_p > p:
                        low_p = p
                        intervalles_rm = n_intervalle_rm
                        nouvelle_intervalle = n_nouvelle_intervalle
                        changing_intervalle = n_changing_intervalle
                        nb_tuple_rm = nb_tuple_to_remove
                        a_effacer = t
                if low_p < 0.1:  # Condition pour essayer de ne pas faire toute les combinaisons possible
                    return low_p, intervalles_rm, changing_intervalle, nouvelle_intervalle, a_effacer, nb_tuple_rm
        return low_p, intervalles_rm, changing_intervalle, nouvelle_intervalle, a_effacer, nb_tuple_rm

    def drill(self, zone, nb_tuple):
        """
        Cette méthode permet de créer un nouvel intervalle de boundary zone avec nb_tuple tuples.
        :param zone: Correspond à la zone à creuser
        :param nb_tuple: Nombre de tuple présent dans la zone à creuser
        :return: None
        """
        if zone == self.bound:
            self.nb_tuple = nb_tuple
        elif self.v() - volume(zone) < epsilon:
            n_b, _ = self.father.merge_pc(self)
            for child in n_b.children:
                # On est obligé de s'assurer d'avoir bien rattaché le bon père !
                child.father = self.father
                if child.intersect(zone) and not child.est_inclus(zone):
                    raise ValueError("Un des fils chevauchait-il self ?")
            self.father.children = n_b.children
            self.father.nb_tuple = n_b.nb_tuple
            self.father.howasicreated = 3
            self.father.drill(zone, nb_tuple)
            # TODO : Remove :
            if self.father.v() < epsilon:
                raise ValueError("Creuser ne fonctionne pas bien")
        else:
            # Création d'un nouvel intervalle
            b_n = Stholes(self.dim_name, self.nb_max_bucket)
            b_n.nb_tuple = nb_tuple
            b_n.bound = deepcopy(zone)
            b_n.father = self
            b_n.howasicreated = 2
            if not self.contient(zone):
                raise ValueError("Le nouvel intervalle n'est pas inclus dans le père !")
            for child in reversed(self.children):
                if child.est_inclus(b_n.bound):
                    child.father = b_n  # Bien penser à réassocier les fils au bon père !
                    b_n.children.append(child)
                    self.children.remove(child)
                elif child.intersect(b_n.bound):
                    raise ValueError("Un des fils coupe la zone à creuser !")
            self.children.append(b_n)
            self.nb_tuple = max(0, self.nb_tuple - nb_tuple)

    def shrink(self, bound_requete, nb_tuple):
        """
        Cette méthode réduit la requête de manière à créer une zone qui ne chevauche pas les autres intervalles.
        :param bound_requete:
        :return:
        """
        trou_candidat = [[max(self.bound[dim][0], bound_requete[dim][0]),
                        min(self.bound[dim][1], bound_requete[dim][1])] for dim in range(len(self.bound))]

        # Liste des enfants qui intersect la requêtes partiellement ====================================================
        participants = []
        for child in self.children:
            # On fait la liste des fils participant ====================================================================
            if child.intersect(trou_candidat) and not child.est_inclus(trou_candidat):
                participants.append(child)
        # Recherche de la dimension où couper ==========================================================================
        while participants:
            max_red = 0
            ou_couper = 0
            for p in participants:
                for dim in range(len(self.bound)):
                    # Cette condition vérifie que seulement l'un des bords de l'intervalle est inclus dans trou_candidat
                    if trou_candidat[dim][0] < p.bound[dim][0] < trou_candidat[dim][1]:
                        tmp = deepcopy(trou_candidat)
                        tmp[dim][1] = p.bound[dim][0]
                        cur_red = self.v_inter(tmp)
                        if max_red <= cur_red:
                            max_red = cur_red
                            ou_couper = dim, 1, p.bound[dim][0]
                    # Code symètrique mais on test l'autre bord
                    if trou_candidat[dim][0] < p.bound[dim][1] < trou_candidat[dim][1]:
                        tmp = deepcopy(trou_candidat)
                        tmp[dim][0] = p.bound[dim][1]
                        cur_red = self.v_inter(tmp)
                        if max_red <= cur_red:
                            max_red = cur_red
                            ou_couper = dim, 0, p.bound[dim][1]
            trou_candidat[ou_couper[0]][ou_couper[1]] = ou_couper[2]
            tab_rm = []

            # Mise à jour des participants =============================================================================
            # Après avoir coupé, il faut vérifier que l'on n'ait pas rajouté un candidat qui était inclus
            for child in self.children:
                if child.intersect(trou_candidat) and not child.est_inclus(trou_candidat) and child not in participants:
                    participants.append(child)
            for p in reversed(participants):
                if not p.intersect(trou_candidat):  # Si le participant n'intersectionne pas la zone c on l'enlève
                    participants.remove(p)
        # Calcul du nombre d'élément dans le trou candidat =============================================================
        v_trou_candidat = 1  # Volume du trou candidat
        for dim in trou_candidat:
            v_trou_candidat *= (dim[1] - dim[0])
        # On retire au volume du trou candidat le volume des trous qui l'intersect =====================================
        for child in self.children:
            if child.est_inclus(trou_candidat):
                v_trou_candidat -= child.vBox()
        v_int = self.v_inter(bound_requete)  # Volume intervalle avant le shrink
        # Le min est la pour les problèmes d'arrondi
        x = min(v_trou_candidat / v_int, 1) # TODO : Problème ici sur le calcul du rapport de volume
        T = nb_tuple * x  # Estimation du nombre de tuple dans le trou candidat
        for c in self.children:
            if c.intersect(trou_candidat) and not c.est_inclus(trou_candidat):
                raise ValueError('Un des fils intersectionne le trou candidat')
        return trou_candidat, T

    def expand_root(self, requete):
        """
                                        /!\ À n'utiliser que sur la racine /!\
        Cette fonction permet d'augmenter la taille de l'boundary de amnière à ce qu'il contienne la requête prise en
        paramètre.
        :param requete:
        :return:
        """
        if self.father is not None:
            raise ValueError("Cette méthode ne doit être utilisée que sur la racine !")
        if not self.bound:
            self.bound = copy(requete[0])
        else:
            for dim in range(len(self.bound)):
                if requete[0][dim][0] < self.bound[dim][0]:
                    self.bound[dim] = [requete[0][dim][0], self.bound[dim][1]]
                if requete[0][dim][1] > self.bound[dim][1]:
                    self.bound[dim] = [self.bound[dim][0], requete[0][dim][1]]

    def estimer(self, bound, dim_a_estimer):
        """
        Renvoie une estimation du nombre d'éléments dans la zone délimitée par bound. Les dimensions de l'intervalle à
        estimer doivent être décris dans le paramètre dim_a_estimer.
        exemple : bound = ([0,1]) dim_a_estimer = ([x])
        Le nom des dimensions doit correspondre aux noms donné dans la variable self.dim_name
                :param bound:
        :return:
        """
        # Calcul du volume de l'intersection entre l'intervalle et du volume totale de l'intervalle dans ces dimensions
        def volume_inter(bound1, bound2, dim_a_estimer, dim_name):
            """
            Fonction intermédiaire pour calculer le volume de l'intersection entre l'intervalle et la requête.
            Renvoit aussi le volume total de l'intervalle de manière à faire le calcul du nombre d'élément.
            """
            volume = 1
            vol_tot = 1
            for i in range(len(dim_a_estimer)):
                id_dim = dim_name.index(dim_a_estimer[i])
                vol_tot *= (bound1[id_dim][1] - bound1[id_dim][0])
                if bound2[i][0] <= bound1[id_dim][0] < bound1[id_dim][1] <= bound2[i][1]:
                    volume *= (bound1[id_dim][1] - bound1[id_dim][0])
                elif bound1[id_dim][0] <= bound2[i][0] < bound2[i][1] <= bound1[id_dim][1]:
                    volume *= (bound2[id_dim][1] - bound2[id_dim][0])
                elif bound1[id_dim][0] <= bound2[i][0] < bound1[id_dim][1]:
                    volume *= (bound1[id_dim][1] - bound2[i][0])
                elif bound1[id_dim][0] < bound2[i][1] <= bound1[id_dim][1]:
                    volume *= (bound2[i][1] - bound1[id_dim][0])
                else:
                    volume = 0
                i += 1
            return volume, vol_tot

        v, vol_tot = volume_inter(self.bound, bound, dim_a_estimer, self.dim_name)

        for child in self.children:
            v_child, v_tot_child = volume_inter(child.bound, bound, dim_a_estimer, self.dim_name)
            v -= v_child
            vol_tot -= v_tot_child
        if vol_tot < epsilon:
            res = 0
        else:
            v = min(v, vol_tot)  # Il est possible que suite à un problème de virgule flotante, le vol_tot soit plus
            # petit que v, on essaie de pallier à ce problème ne forçant l'égalité en cas de problème
            res = self.nb_tuple * (v/vol_tot)
        for child in self.children:
            res += child.estimer(bound, dim_a_estimer)
        return res

    def vBox(self):
        """
        Cette fonction renvoit le volume brut d'un boundary. C'est à dire le produit des longuers de l'boundary dans
        chaque dimensions.
        :return:
        """
        volume = 1
        for b in self.bound:
            volume *= (b[1] - b[0])
        return volume

    def v(self):
        """
        Renvoit le volume d'un boundary, c'est à dire le volume brut de l'boundary auquel on retranche le volume de
        ces fils.
        :return:
        """
        return self.vBox() - sum([child.vBox() for child in self.children])

    def vBox_inter(self, bound):
        """
        Cette fonction renvoit le volume brut d'un intervalle inter une requête. C'est à dire le produit des longueurs de
        l'intervalle dans chaque dimensions.
        :return:
        """
        volume = 1
        if self.intersect(bound) or self.est_inclus(bound):
            for dim in range(len(self.bound)):
                x1 = max(bound[dim][0], self.bound[dim][0])
                x2 = min(bound[dim][1], self.bound[dim][1])
                volume *= (x2 - x1)
        else:
            volume = 0
        return volume

    def v_inter(self, req_bound):
        """
        Recquiert au préallable d'avoir testé si la requête et l'intervalle se chevauchent.
        Renvoit le volume de l'intersection entre l'intervalle et une frontière (bound).
        :param bound: frontière de la zone généralement correspond à une requête.
        :return:
        """
        if self.intersect(req_bound):
            res = self.vBox_inter(req_bound)
            for child in self.children:
                res -= child.vBox_inter(req_bound)
        else:
            res = 0
        return res

    def count_nb_bucket(self):
        """
        Remonte au noeud père puis lance la méthode count_your_child de manière récurrente.
        :return: Le nombre d'intervalle que contient l'histogramme.
        """
        current_bucket = self
        while current_bucket.father is not None:  # On cherche l'boundary racine
            current_bucket = current_bucket.father
        # On utilise une fonction récursive pour compter le nombre d'boundary crée juqu'à maintenant
        return current_bucket.count_your_child()

    def count_your_child(self):
        """
        Compte le nombre d'enfant que possède un noeud puis envoie la méthode de manière récursive.
        :return:
        """
        nb_child = len(self.children)
        for child in self.children:
            nb_child += child.count_your_child()
        return nb_child

    def contient(self, bound):
        """
        Renvoit un booléen indiquant si l'intervalle contient l'intervalle définis par la frontière.
        :param bound:
        :return:
        """
        contient = True
        dim = 0
        while dim < len(self.bound) and contient:
            contient = (self.bound[dim][0] <= bound[dim][0] < bound[dim][1] <= self.bound[dim][1])
            dim += 1
        return contient

    def est_inclus(self, bound):
        """
        Renvoit un booléen indiquant si l'intervalle est inclus dans l'intervalle définis par la frontière.
        :param bound: la frontière
        :return:
        """
        est_inclus = True
        dim = 0
        while dim < len(self.bound) and est_inclus:
            if not (bound[dim][0] <= self.bound[dim][0] < self.bound[dim][1] <= bound[dim][1]):
                est_inclus = False
            dim += 1
        return est_inclus

    def get_size(self):
        size_node = getsizeof(self.nb_tuple)
        size_node += getsizeof(self.dim_name)
        size_node += getsizeof(self.bound)
        for child in self.children:
            size_node += child.get_size()
        return size_node

    def nb_tot_tuple(self):
        # TODO : rm test purposes only
        nb = self.nb_tuple
        for child in self.children:
            nb += child.nb_tot_tuple()
        return nb

    def intersect(self, bound_requete):
        """
        Renvoit si l'intervalle définit par la frontière intersectionne la requête.
        :param bound:
        :param requete:
        :return:
        """
        for dim in range(len(self.bound)):
            if self.bound[dim][0] < bound_requete[dim][0]:
                if self.bound[dim][1] <= bound_requete[dim][0]:
                    return False  # La requête et l'intervalle ne s'intersectionne pas !
            else:
                if self.bound[dim][0] >= bound_requete[dim][1]:
                    return False
        return True

    def save(self, path):
        f = open(path+'.histo', 'wb')
        dump(self, f)
        f.close()

    def print(self, debug_it=False):
        tab = [((self.bound[0][0], self.bound[1][0]),
                self.bound[0][1] - self.bound[0][0],
                self.bound[0][1] - self.bound[1][0])]
        for c in self.children:
            tab += c.print()

        if self.father is None or debug_it:
            # couleur = ['r', 'g', 'c', 'm', 'y', 'k', 'w']
            figure = plt.figure()
            axes = plt.axes()
            axes.set_xlim(left=min(self.bound[0]), right=max(self.bound[0]))
            axes.set_ylim(bottom=min(self.bound[1]), top=max(self.bound[0]))
            axes.set_xlabel(self.dim_name[0])
            axes.set_ylabel(self.dim_name[1])
            subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
            for t in tab:
                subplot.add_patch(patches.Rectangle(t[0], t[1], t[2], linewidth=1, fill=False))
            plt.show()
        else:
            return tab


def volume(zone):
    res = 1
    for b in zone:
        res *= (b[1] - b[0])
    return res