"""
:author : Cyril MOINEAU
:creation_date : 02/03/20
:last_change_date : 02/03/20
:description : Création de requêtes aléatoire permettant de donner de construire l'histogramme STHOLES

Définition :
    - Une requête est définis comme [([centres], [longueurs]) for each dim]
"""
import random as random
import matplotlib.pyplot as plt
from matplotlib import patches
from utils import est_inclus


def create_workload(data, volume, nb_query):
    requetes = []
    for _ in range(nb_query):
        centres = []
        longueurs = []
        for d in data:
            centres.append(random.uniform(min(d), max(d)))
            longueurs.append(random.random() * (max(d)-min(d))*(volume**(1/len(data))))
        bound = [[(centres[dim] - (longueurs[dim] / 2)), (centres[dim] + (longueurs[dim] / 2))] for dim in
                 range(len(data))]
        nb_tuple = 0
        for i in range(len(data[0])):
            point = [d[i] for d in data]
            if est_inclus(point, bound):
                nb_tuple += 1
        requetes.append((bound, nb_tuple))
    return requetes


def print_workload(requetes):
    """
    Affciche sous forme de rectangle les requêtes généré aléatoirement
    :param requetes:
    :return:
    """
    figure = plt.figure()
    axes = plt.axes()
    axes.set_xlim(left=-10, right=10)
    axes.set_ylim(bottom=-10, top=10)
    subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
    for r in requetes:
        bound = [r[0][i] - (r[1][i]/2) for i in range(len(r[0]))]
        w = r[1][0]
        h = r[1][1]
        subplot.add_patch(patches.Rectangle(bound, w, h, linewidth=1, fill=False))
    plt.plot()
    plt.show()