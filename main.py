"""
:author : Cyril MOINEAU
:creation_date : 12/02/20
:last_change_date : 17/03/20
:description : Script principale permettant de tester les différents histogrammes.
"""

import MHIST.Mhist as mhist
import GENHIST.Genhist as genhist
import AVI.avi as avi
import STHOLES.Stholes as st
import utils
from STHOLES import Workload as w
import matplotlib.pyplot as plt
import time
import numpy as np


def test_mhist(tab_attribut, nom_dim, dim_estimer, intervalle_estimer):
    # Initialisation des paramètres ====================================================================================
    nombre_intervalle = 500

    # Création de l'histogramme ========================================================================================
    histogramme = mhist.Mhist(tab_attribut, nom_dim, nombre_intervalle)

    # Test =============================================================================================================
    x = round(histogramme.estimate(dim_estimer, intervalle_estimer))
    print("Résultat estimé avec MHIST :   ", x)

    # Affichage de l'histogramme =======================================================================================
    histogramme.print(nom_dim[:2])
    plt.scatter(tab_attribut[[nom_dim.index(d_e) for d_e in dim_estimer][0]],
                tab_attribut[[nom_dim.index(d_e) for d_e in dim_estimer][1]])
    plt.show()


def test_genhist(tab_data, nom_dim, dim_estimer, intervalle_estimer):
    # Initialisation des paramètres ====================================================================================
    b = 500
    xi = 30  # Qu'elle est une valeur classique ?
    alpha = (1/2)**(1/len(tab_data))
    tab_data = tab_data.copy().tolist()  # Je fais une copie du tableau d'intervalle sous la forme d'une liste

    # Création de l'histogramme ========================================================================================
    histogramme = genhist.Genhist(tab_data, nom_dim, b, xi, alpha, verbeux=False)

    # Test =============================================================================================================

    # print('nb_tot de tuple : ', histogramme.estimate(histogramme.dim_name, [[min(d), max(d)] for d in tab_data]))
    # print('Résultat estimé : ', histogramme.estimate(dim_estimer, intervalle_estimer))

                                #########################################
                                # TEST POUR TROUVER MEILLEUR XI ET B    #
                                #########################################

    workload = w.create_workload(tab_data, 0.1, 200)

    # test_b = []
    # for b in range(25, 200):
    #     histogramme = genhist.Genhist(tab_data, nom_dim, b, xi, alpha, verbeux=False)
    #     moy = 0
    #     cpt = 0
    #     # workload = w.create_workload(tab_attribut, 0.05, 500)
    #     for r in workload:
    #         est = histogramme.estimate(histogramme.dim_name, r[0])
    #         if r[1] != 0:
    #             err = (abs(est - r[1]) / r[1])
    #             # print("Estimation :", est, " Reel :", r[1], "Erreur :", err, " Bound :", r[0])
    #             # print("\n")
    #             moy += err
    #             cpt += 1
    #         # else:
    #         #     print("Estimation :", est, " Reel :", r[1], " Bound :", r[0])
    #         #     print("\n")
    #     # print("Erreur moyenne : ", moy / cpt)
    #     test_b.append(moy / cpt)
    # plt.plot(test_b)
    # plt.show()

    test_xi = []
    b = 80
    val_xi = range(5, 50)
    for xi in val_xi:
        histogramme = genhist.Genhist(tab_data, nom_dim, b, xi, alpha, verbeux=False)
        moy = 0
        cpt = 0
        # workload = w.create_workload(tab_attribut, 0.05, 500)
        for r in workload:
            est = histogramme.estimate(histogramme.dim_name, r[0])
            if r[1] != 0:
                err = (abs(est - r[1]) / r[1])
                # print("Estimation :", est, " Reel :", r[1], "Erreur :", err, " Bound :", r[0])
                # print("\n")
                moy += err
                cpt += 1
            # else:
            #     print("Estimation :", est, " Reel :", r[1], " Bound :", r[0])
            #     print("\n")
        # print("Erreur moyenne : ", moy / cpt)
        test_xi.append(moy / cpt)
    plt.plot(test_xi)
    plt.show()

    # Affichage de l'histogramme =======================================================================================
    # histogramme.print()
    # plt.scatter(tab_attribut[[nom_dim.index(d_e) for d_e in dim_estimer][0]],
    #             tab_attribut[[nom_dim.index(d_e) for d_e in dim_estimer][1]])
    # plt.show()


def test_st(tab_attribut, nom_dim, dim_estimer, intervalle_estimer):
    nb_intervalle = 500
    nb_req_entrainement = 100
    # Création de l'histogramme ========================================================================================
    histogramme = st.Stholes(nom_dim, nb_intervalle, verbeux=False)
    print("Création d'un set d'entraînement pour ST-Holes ...")
    workload = w.create_workload(tab_attribut, 0.01, nb_req_entrainement)
    print("Lancement de la construction de St-Holes !")

    # On commence avec une requête sur l'ensemble des données
    histogramme.BuildAndRefine([([[min(a), max(a)] for a in tab_attribut], len(tab_attribut[0]))])
    histogramme.BuildAndRefine(workload)
    # x = round(histogramme.estimer(intervalle_estimer, dim_estimer))
    # x = round(histogramme.estimer(histogramme.bound[:2], histogramme.dim_name[:2]))
    # print("Résultat estimé avec STHOLES : ", x, "nb_tot_tuple", histogramme.nb_tot_tuple())
    moy = 0
    cpt = 0
    # workload = w.create_workload(tab_attribut, 0.05, 500)
    for r in workload:
        est = histogramme.estimer(r[0], histogramme.dim_name)
        if r[1] != 0:
            err = (abs(est - r[1]) / r[1])
            print("Estimation :", est, " Reel :", r[1], "Erreur :", err, " Bound :", r[0])
            print("\n")
            moy += err
            cpt += 1
        else:
            print("Estimation :", est, " Reel :", r[1], " Bound :", r[0])
            print("\n")
    print("Erreur moyenne : ", moy / cpt)
    x = round(histogramme.estimer(histogramme.bound, histogramme.dim_name))
    print("Résultat estimé avec STHOLES : ", x, "nb_tot_classe", histogramme.count_nb_bucket())
    print(histogramme.bound)
    histogramme.print()
    # histogramme.save('./STHoles')


def test_avi(tab_attribut, nom_dim, dim_estimer, intervalle_estimer):
    o_avi = avi.Avi(tab_attribut)
    x = round(o_avi.estimation([nom_dim.index(d_e) for d_e in dim_estimer], intervalle_estimer))
    print("Résultat estimé avec AVI :     ", x)


if __name__ == '__main__':
    # Lecture des données ==============================================================================================
    path = "./DATA/fake_data.txt"
    att1 = []
    att2 = []
    att3 = []
    with open(path, "r") as f:
        for line in f:
            line = line.split(',')
            att1.append(float(line[0]))
            att2.append(float(line[1]))
            att3.append(float(line[2]))

    # Paramètres =======================================================================================================

    att1_square = np.array(att1).copy() ** 2
    att2_lin = np.array(att1).copy() * 2

    tab_attribut = np.array([att1, att2])
    nom_dim = ['x', 'y']

    intervalle_estimer = [(-1, 1), (-1, 1)]
    dim_estimer = ['x', 'y']

    # Calcul des coefficients de corrélation ===========================================================================
    # correl.calcul_des_correlations(tab_attribut)
    utils.coef_correlation(tab_attribut)

    # Lancement des tests ==============================================================================================
    print('===============================================TEST======================================================')

    print("On veut estimer le nombre de tuple dans l'intervalle : ", dim_estimer, intervalle_estimer)

    # Affichage des vraies valeurs à estimer ===========================================================================
    nb_tuple = len(tab_attribut[0])
    res = 0
    t = time.time()
    for i in range(nb_tuple):
        if utils.est_inclus([att[i] for cpt, att in enumerate(tab_attribut) if (nom_dim[cpt] in dim_estimer)], intervalle_estimer):
            res += 1
    print("Résultat réel :                 " + str(round(res)) + ' calculé en ' + str(time.time() - t) + ' s')

    # test_avi(tab_attribut, nom_dim, dim_estimer, intervalle_estimer)
    # test_st(tab_attribut, nom_dim, dim_estimer, intervalle_estimer)
    # test_mhist(tab_attribut, nom_dim, dim_estimer, intervalle_estimer)
    test_genhist(tab_attribut, nom_dim, dim_estimer, intervalle_estimer)

