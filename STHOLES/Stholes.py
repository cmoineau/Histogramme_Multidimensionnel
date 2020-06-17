"""
:author : Cyril MOINEAU
:creation_date : 02/03/20
:last_change_date : 23/04/20
:description : Définition d'un histogramme ST-Holes.

Définitions :
    - requête : [ [intervalles], nombre de tuple renvoyé par la requête ]
    - boundary : (frontière) : [[intervalle d'une classe] for dim in nb_dim ]

"""

from sys import getsizeof
from copy import deepcopy, copy
from utils import epsilon
from pickle import dump
import matplotlib.pyplot as plt
from matplotlib import patches


class Stholes(object):
    def __init__(self, dim_name, nb_max_bucket, verbeux=False):
        """
        Un histogramme ST-Holes est un histogramme qui peut se définir comme un arbre. Une classe correspond à un
        histogramme St-Holes. On retrouve des notions tel que celle d'boundary (i.e: noeud) fils ou père.
        Cet histogramme est particulier car il se construit sans regarder les données.
        Ce constructeur produit un histogramme vide, il conviendra d'utiliser la fonction 'BuildAndRefine' et
        'build_and_refine' pour le mettre à jour.
        :param dim_name:
        :param nb_max_bucket:
        :param verbeux:
        """
        self.nb_tuple = 0  # Nombre de tuple inclus dans la classe
        self.children = []  # Liste des enfants (classe inclus dans la classe courante)
        self.intervalles = []  # liste des intervalles qui définis la classe (forme un hyperplan)
        self.nb_max_classes = nb_max_bucket  # nombre de classe a ne pas dépasser dans l'histogramme
        self.attributes_name = dim_name  # Un tableau listant le nom des attributs
        self.father = None  # Lien vers le père de la classe courante (None pour la racine)
        self.howasicreated = None  # Seulement pour débugger, permet de savoir comment à été crée la classe
                                   # 0 : Fusion ss, 1 : Fusion pc, 2 : Drill
        self.verbeux = verbeux
        self.penalities= {}  # Dictionnaire clef = classe
                             #              valeur = [classe_meilleur_fusion, penalité]
        # Note : Le tableau des pénalités ne teste que la classe père et les classes "soeur", on ne test pas les fils
        # car ils testent leur père ce qui suffit grâce à la symétrie de la fusion.

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
            # On creuse les trous en fonction des requêtes =============================================================
            for intervalle in tab:
                intervalle[0].shrink_and_drill(requete[0], intervalle[1])

            # print('Nb tuple dans la requête :', requete[1])
            # self.print()
            # Suppression des intervalles excedentaire =================================================================
            while self.count_nb_bucket() > self.nb_max_classes:
                if self.verbeux:
                    print('Suppression ... encore ', self.count_nb_bucket() - self.nb_max_classes, ' buckets')
                self.delete_bucket()

        if self.verbeux:
            print('Fin de la mise à jour !')

    def delete_bucket(self):
        """
        Cette méthode supprime une classe de l'intervalle en fusionnant deux classes. La fusion réalisé est celle qui
        permet de perdre le moins d'information possible !
        :return:
        """
        # Recherche de la plus faible pénalité =========================================================================
        # INITIALISATION
        min_p = None
        b1 = None
        b2 = None
        fusion_pc = False
        # DEBUT
        for key, value in self.penalities.items():
            if min_p is None or value[1] < min_p:
                min_p = value[1]
                b1 = key
                b2 = value[0]
        # CAS FUSION PC
        if b1.father is b2:  # Cas où b2 est le père de b1
            fusion_pc = True
            new_bucket, _ = b2.merge_pc(b1)
            nb_tuple_to_remove = None
            bucket_rm = [b2]
            changing_bucket = b2.father
        # CAS FUSION SS
        elif b1 in b2.father.children and b2 in b1.father.children:  # Cas où b1 et b2 sont frère
            n_b, penality, to_rm, nb_tuple_rm = b1.father.merge_ss(b1, b2)
            bucket_rm = to_rm
            changing_bucket = b1.father
            new_bucket = n_b
            nb_tuple_to_remove = nb_tuple_rm
        else:
            raise ValueError("L'on n'est ni dans un cas pc ni ss erreur d'attribution de fils à un père ?")

        # L'intervalle résultant de la fusion annonce le changement de père au fils
        for child in new_bucket.children:
            child.father = new_bucket

        if new_bucket.father is None:
            # Dans ce cas on à fait une fusion avec la racine, on ne la supprime pas mais on la màj
            del self.penalities[b1]  # On supprime le fils qui a fusionné
            self.nb_tuple = new_bucket.nb_tuple
            self.children = new_bucket.children
            for child in new_bucket.children:
                child.father = self
            self.intervalles = new_bucket.intervalles
            self.howasicreated = new_bucket.howasicreated
            new_bucket = None  # Pour s'assurer qu'on le détruise (necessaire ?)
            # On màj les classes qui avaient une meilleure fusion avec b1 (le fils fussioné)
            for classe in self.children:
                #  Ici on regarde les anciens fères de b1
                if self.penalities[classe][0] is b1:
                    classe.update_penalities()
            for classe in b1.children:
                #  Ici on regarde les anciens fils de b1
                if self.penalities[classe][0] is b1:
                    classe.update_penalities()
        else:
            del self.penalities[b1]
            del self.penalities[b2]
            for r in bucket_rm:
                changing_bucket.children.remove(r)
            if nb_tuple_to_remove is not None:
                changing_bucket.nb_tuple -= nb_tuple_to_remove
            changing_bucket.children.append(new_bucket)
            new_bucket.update_penalities()
            if fusion_pc:
                for c in changing_bucket.children:
                    # Maj des frère de b2 qui pointaient vers b2
                    if c is not b2 and self.penalities[c][0] is b2:
                        c.update_penalities()
                for c in b1.children:
                    # Màj des fils de b1 qui pointaient vers b1
                    if self.penalities[c][0] is b1:
                        c.update_penalities()
                for c in b2.children:
                    # Màj des frères de b1 qui pointaient vers b1
                    if c is not b1 and self.penalities[c][0] is b1:
                        c.update_penalities()
                    # Màj des fils de b2 qui pointaient vers b2
                    if c is not b1 and self.penalities[c][0] is b2:
                        self.penalities[c][0] = new_bucket
            else:
                for c in new_bucket.children:
                    #  On regarde si les enfants n'étaient pas rattaché à leur ancien père ou aux classes qui ont servis
                    #  à la fusion.
                    if self.penalities[c][0] is changing_bucket \
                            or self.penalities[c][0] is b1 \
                            or self.penalities[c][0] is b2:
                        c.update_penalities()
                    # on màj si des anciens frères se retrouvent séparé
                    for c0 in changing_bucket.children:
                        if self.penalities[c][0] is c0:
                            c.update_penalities()
                for c in changing_bucket.children:
                    #  On regarde si les enfants n'étaient pas rattachés aux classes qui ont servis à la fusion.
                    if self.penalities[c][0] is b1 \
                       or self.penalities[c][0] is b2:
                        c.update_penalities()
                    for c0 in new_bucket.children:
                        if self.penalities[c][0] is c0:
                            c.update_penalities()

    def nb_tuple_intervalles(self, requete):
        """
        Renvoit la liste des classes en intersection avec la requête avec le nombre de tuple de la requête qui tomb dans
        la classe.
        Utilise une recherche top-down de l'arbre .
        :param requete:
        :return:
        """
        tab_res = []
        if self.vBox_inter(requete[0]) > epsilon:
            volume_requete = 1
            v_int = self.v_inter(requete[0])
            for dim in range(len(requete[0])):
                volume_requete *= (requete[0][dim][1]-requete[0][dim][0])
            x = min(v_int / volume_requete, 1)
            nb_tuple_dans_intervalle = requete[1] * x
            if v_int > epsilon:  # Si le volume intérieur est non nul ie si la requête ne tombe pas dans un fils
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
        if self.estimer(c1, self.attributes_name) != T1:
            self.drill(c1, T1)

    def merge_pc(self, child):
        """
        :param child:
        :return: Renvoit l'intervalle qu'on obtiendrait en fusionnant un père (self) avec l'un de ses fils. Ainsi que la
        pénalité associée à cette fusion.
        """
        # Creation du nouvel intervalle ================================================================================
        n_b = Stholes(self.attributes_name, self.nb_max_classes)
        n_b.penalities = self.penalities
        n_b.nb_tuple = self.nb_tuple + child.nb_tuple
        n_b.father = self.father
        n_b.intervalles = self.intervalles
        n_b.howasicreated = 1
        for c in self.children:
            if c is not child:
                n_b.children.append(c)
        for c in child.children:
            n_b.children.append(c)
        # Calcul de la pénalitée =======================================================================================
        # penality = abs(self.nb_tuple - n_b.estimer(self.intervalles, self.attributes_name)) + \
        #            abs(self.estimer(child.intervalles, self.attributes_name) - n_b.estimer(child.intervalles, self.attributes_name))
        penality = abs(self.nb_tuple - n_b.nb_tuple * (self.v() / n_b.v()) +
                       abs(child.nb_tuple - n_b.nb_tuple * (child.v() / n_b.v())))
        return n_b, penality

    def merge_ss(self, child1, child2):
        """
        :param child:
        :return: Renvoit l'intervalle qu'on obtiendrait en fusionnant un de fils de self. Ainsi que la pénalité associée
        à cette fusion et une liste d'intervalle appartenant à self qui appartiendrait à l'intervalle obtenu suite à la
        fusion.
        """
        if self.v() == 0:
            # Dans ce cas, les fils occupent tout l'espace, il faut fusionner les fils pour faire une fusion père fils plus tard
            return None, None, None, None
        # Création du nouvelle intervalle ==============================================================================
        n_b = Stholes(self.attributes_name, self.nb_max_classes)
        n_b.penalities = self.penalities
        n_b.father = child1.father
        n_b.intervalles = [[min(child1.intervalles[dim][0], child2.intervalles[dim][0]), max(child1.intervalles[dim][1], child2.intervalles[dim][1])]
                           for dim in range(len(self.intervalles))]
        n_b.howasicreated = 0
        for c in child1.children:
            n_b.children.append(c)
        for c in child2.children:
            n_b.children.append(c)

        # Liste des classes à tester pour savoir si elles intersectent le résultat de la fusion ========================
        a_verifier = copy(self.children)
        a_verifier.remove(child1)
        a_verifier.remove(child2)
        to_rm = [child1, child2]  # Liste des classes à enlever du père si l'on selectionne cette fusion.

        # Le parcours qui suit de la liste des classes à vérifier est un peu particulier, on ne retire des classes de
        # la liste que si la classe est incluse dans le résultat de la fusion. L'idée étant que si l'on agrandit la
        # fusion, une classe qui n'intersectionnait pas la fusion peut à nouveau intersectionner la fusion.
        # On fait aussi un parcours en partant de la fin de la liste afin de pouvoir supprimer les éléments sans
        # problème.
        cpt = len(a_verifier)-1
        while cpt >= 0:
            current = a_verifier[cpt]
            change_la_taille = False
            if current.est_inclus(n_b.intervalles):
                to_rm.append(current)
                n_b.children.append(current)
                a_verifier.remove(current)
            elif current.intersect(n_b.intervalles):
                for dim in range(len(n_b.intervalles)):
                    if n_b.intervalles[dim][0] <= current.intervalles[dim][0] <= n_b.intervalles[dim][1] <= current.intervalles[dim][1]:
                        # la classe courante dépasse à droite
                        n_b.intervalles[dim][1] = current.intervalles[dim][1]
                        change_la_taille = True
                    elif current.intervalles[dim][0] <= n_b.intervalles[dim][0] <= current.intervalles[dim][1] <= n_b.intervalles[dim][1]:
                        # la classe courante dépasse à gauche
                        n_b.intervalles[dim][0] = current.intervalles[dim][0]
                        change_la_taille = True
                    elif current.intervalles[dim][0] <= n_b.intervalles[dim][0] <= n_b.intervalles[dim][1] <= current.intervalles[dim][1]:
                        # la classe courante dépasse des deux côtés
                        n_b.intervalles[dim][0] = current.intervalles[dim][0]
                        n_b.intervalles[dim][1] = current.intervalles[dim][1]
                        change_la_taille = True
            if change_la_taille:
                to_rm.append(current)
                n_b.children.append(current)
                a_verifier.remove(current)
                cpt = len(a_verifier)-1
            else:
                cpt -= 1

        # Calcul du nombre de tuple ====================================================================================
        # p = père, n = nouveau
        # vold correspond au volume qu'occupait le père à la place de la fusion.
        vold = n_b.vBox() - sum([intervalle.vBox() for intervalle in to_rm])
        # vn correspond au volume de la nouvelle
        vn = vold + child1.vBox() + child2.vBox()
        nb_tuple_to_rm_from_p = self.nb_tuple * (vold / self.v())
        n_b.nb_tuple = nb_tuple_to_rm_from_p + child1.nb_tuple + child2.nb_tuple
        # Calcul de la pénalitée ===================================================================================
        # Pénalité du à l'estimation de la zone "old"
        p1 = abs(self.nb_tuple * (vold / self.v()) - n_b.nb_tuple * (vold / n_b.v()))
        # Pénalité dû à l'estimation du fils 1
        p2 = abs(child1.nb_tuple - n_b.nb_tuple * (child1.v() / vn))
        # Pénalité dû à l'estimation du fils 2
        p3 = abs(child2.nb_tuple - n_b.nb_tuple * (child2.v() / vn))
        penality = p1 + p2 + p3
        return n_b, penality, to_rm, nb_tuple_to_rm_from_p

    def update_penalities(self):
        if self.father is not None:
            if self not in self.father.children:
                raise ValueError("F")
            _, penality = self.father.merge_pc(self)
            best_p = penality
            best_c = self.father
            for c in self.father.children:
                if c is not self:
                    if c.father is not self.father:
                        raise ValueError("F")
                    _, penality, _, _ = self.father.merge_ss(self, c)
                    if penality is not None and penality < best_p:
                        best_p = penality
                        best_c = c
            self.penalities[self] = [best_c, best_p]

    def drill(self, zone, nb_tuple):
        """
        Cette méthode permet de créer un nouvel intervalle de boundary zone avec nb_tuple tuples.
        :param zone: Correspond à la zone à creuser
        :param nb_tuple: Nombre de tuple présent dans la zone à creuser
        :return: None
        """
        if zone == self.intervalles:
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
            del self.penalities[self]
            for child in self.father.children:
                # On ne met pas à jour les fils qui pointaient vers le père car le père est souvent très proche  du
                # résultat de la fusion.
                if self.penalities[child][0] is self:
                    # On màj les frères qui pointaient sur self
                    child.update_penalities()
            for child in self.children:
                if self.penalities[child][0] is self:
                    # On màj les fils de self qui pointaient sur self
                    child.update_penalities()
            self.father.drill(zone, nb_tuple)
            # TODO : Remove :
            if self.father.v() < epsilon:
                raise ValueError("Creuser ne fonctionne pas bien")
        else:
            # Création d'un nouvel intervalle
            b_n = Stholes(self.attributes_name, self.nb_max_classes)
            b_n.nb_tuple = nb_tuple
            b_n.intervalles = deepcopy(zone)
            b_n.father = self
            b_n.howasicreated = 2
            b_n.penalities = self.penalities
            tab_class_to_update = []
            if not self.contient(zone):
                raise ValueError("Le nouvel intervalle n'est pas inclus dans le père !")
            for child in reversed(self.children):
                if child.est_inclus(b_n.intervalles):
                    child.father = b_n  # Bien penser à réassocier les fils au bon père !
                    b_n.children.append(child)
                    tab_class_to_update.append(child)
                    self.children.remove(child)
                elif child.intersect(b_n.intervalles):
                    raise ValueError("Un des fils coupe la zone à creuser !")
            tmp = copy(tab_class_to_update)
            self.children.append(b_n)
            self.nb_tuple = max(0, self.nb_tuple - nb_tuple)
            b_n.update_penalities()
            for child in self.children:
                if self.penalities[child][0] in tmp:
                    tab_class_to_update.append(child)
            for c in tab_class_to_update:
                c.update_penalities()

    def shrink(self, bound_requete, nb_tuple):
        """
        Cette méthode réduit la requête de manière à créer une zone qui ne chevauche pas les autres intervalles.
        :param bound_requete:
        :return:
        """
        trou_candidat = [[max(self.intervalles[dim][0], bound_requete[dim][0]),
                          min(self.intervalles[dim][1], bound_requete[dim][1])] for dim in range(len(self.intervalles))]

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
                for dim in range(len(self.intervalles)):
                    # Cette condition vérifie que seulement l'un des bords de l'intervalle est inclus dans trou_candidat
                    if trou_candidat[dim][0] < p.intervalles[dim][0] < trou_candidat[dim][1]:
                        tmp = deepcopy(trou_candidat)
                        tmp[dim][1] = p.intervalles[dim][0]
                        cur_red = self.v_inter(tmp)
                        if max_red <= cur_red:
                            max_red = cur_red
                            ou_couper = dim, 1, p.intervalles[dim][0]
                    # Code symètrique mais on test l'autre bord
                    if trou_candidat[dim][0] < p.intervalles[dim][1] < trou_candidat[dim][1]:
                        tmp = deepcopy(trou_candidat)
                        tmp[dim][0] = p.intervalles[dim][1]
                        cur_red = self.v_inter(tmp)
                        if max_red <= cur_red:
                            max_red = cur_red
                            ou_couper = dim, 0, p.intervalles[dim][1]
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
        x = min(v_trou_candidat / v_int, 1)  # TODO : Problème ici sur le calcul du rapport de volume
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
        if not self.intervalles:
            self.intervalles = copy(requete[0])
        else:
            for dim in range(len(self.intervalles)):
                if requete[0][dim][0] < self.intervalles[dim][0]:
                    self.intervalles[dim] = [requete[0][dim][0], self.intervalles[dim][1]]
                if requete[0][dim][1] > self.intervalles[dim][1]:
                    self.intervalles[dim] = [self.intervalles[dim][0], requete[0][dim][1]]

    def estimer(self, dim_a_estimer, bound):
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
                    volume *= (bound2[i][1] - bound2[i][0])
                elif bound1[id_dim][0] <= bound2[i][0] < bound1[id_dim][1]:
                    volume *= (bound1[id_dim][1] - bound2[i][0])
                elif bound1[id_dim][0] < bound2[i][1] <= bound1[id_dim][1]:
                    volume *= (bound2[i][1] - bound1[id_dim][0])
                else:
                    volume = 0
                i += 1
            return volume, vol_tot

        v, vol_tot = volume_inter(self.intervalles, bound, dim_a_estimer, self.attributes_name)
        if v == 0:  # on est tombé dans le cas sans intersection
            return 0
        for child in self.children:
            v_child, v_tot_child = volume_inter(child.intervalles, bound, dim_a_estimer, self.attributes_name)
            v -= v_child
            vol_tot -= v_tot_child
        if vol_tot < epsilon:  # Cas spécial où l'intervalle est entièrement occupé par ces fils.
            # Il faut le traiter à part pour éviter une division par zéro
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
        for b in self.intervalles:
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
            for dim in range(len(self.intervalles)):
                x1 = max(bound[dim][0], self.intervalles[dim][0])
                x2 = min(bound[dim][1], self.intervalles[dim][1])
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
        Remonte au noeud père puis lance la méthode count_your_child.
        :return: Le nombre d'intervalle que contient l'histogramme.
        """
        current_bucket = self
        while current_bucket.father is not None:  # On cherche l'boundary racine
            current_bucket = current_bucket.father
        # On utilise une fonction récursive pour compter le nombre d'boundary crée juqu'à maintenant
        return current_bucket.count_your_child() + 1

    def count_your_child(self):
        """
        Compte le nombre d'enfant que possède un noeud puis appel la méthode de manière récursive à ses fils.
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
        while dim < len(self.intervalles) and contient:
            contient = (self.intervalles[dim][0] <= bound[dim][0] < bound[dim][1] <= self.intervalles[dim][1])
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
        while dim < len(self.intervalles) and est_inclus:
            if not (bound[dim][0] <= self.intervalles[dim][0] < self.intervalles[dim][1] <= bound[dim][1]):
                est_inclus = False
            dim += 1
        return est_inclus

    def get_size(self):
        size_node = getsizeof(self.nb_tuple)
        size_node += getsizeof(self.attributes_name)
        size_node += getsizeof(self.intervalles)
        size_node += getsizeof(self.penalities)
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
        for dim in range(len(self.intervalles)):
            if self.intervalles[dim][0] < bound_requete[dim][0]:
                if self.intervalles[dim][1] <= bound_requete[dim][0]:
                    return False  # La requête et l'intervalle ne s'intersectionne pas !
            else:
                if self.intervalles[dim][0] >= bound_requete[dim][1]:
                    return False
        return True

    def save(self, path):
        f = open(path, 'wb')
        dump(self, f)
        f.close()

    def print(self, debug_it=False, tab_attribut=None):
        """
        Méthode permettant d'afficher l'histogramme.
        Si vous voulez print un noeud de l'histogramme qui n'est pas le noeud père, il faut passer debug_it à true.
        :param tab_attribut: Tableau de l'ensemble des points [[x], [y]] permet d'afficher les points du jeu de donnée.
        (2D seulement)
        :param debug_it: Boolean pour afficher un noeud qui n'est pas la racine.
        :return: Figure matplotlib du noeud courant et de ces fils.
        """

        tab = [((self.intervalles[0][0], self.intervalles[1][0]),   # Point en bas à gauche
                self.intervalles[0][1] - self.intervalles[0][0],    # Largeur
                self.intervalles[1][1] - self.intervalles[1][0],    # Hauteur
                round(self.nb_tuple))]                                     # Nombre de tuple (pour label)
        for c in self.children:
            tab += c.print()

        if self.father is None or debug_it:
            # couleur = ['r', 'g', 'c', 'm', 'y', 'k', 'w']
            figure = plt.figure()
            axes = plt.axes()
            axes.set_xlim(left=round(min(self.intervalles[0])) - 1, right=max(self.intervalles[0]) + 1)
            axes.set_ylim(bottom=round(min(self.intervalles[1])) - 1, top=max(self.intervalles[0]) + 1)
            axes.set_xlabel(self.attributes_name[0])
            axes.set_ylabel(self.attributes_name[1])
            subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
            for t in tab:
                subplot.add_patch(patches.Rectangle(t[0], t[1], t[2], linewidth=1, fill=False))
                if t[3] != 0.0:  # On n'affiche plus si c'est 0.0 pour plus de lisibilité
                    plt.annotate(str(t[3]), t[0])
            if tab_attribut is not None:
                plt.scatter(tab_attribut[0], tab_attribut[1], marker='+')
            plt.show()
        else:
            return tab


def volume(zone):
    res = 1
    for b in zone:
        res *= (b[1] - b[0])
    return res