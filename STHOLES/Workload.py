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


def create_workload_full(data, volume, nb_query):
    requetes = create_workload(data, volume, nb_query)

    for i in range(len(data[0])):
        print(i, '/', len(data[0]))
        flag = True
        r = 0
        point = [d[0] for d in data]
        while flag and r < len(requetes):
            point = [d[i] for d in data]
            if est_inclus(point, requetes[r][0]):
                flag = False
            r += 1
        if flag:
            centres = point
            longueurs = []
            centres.append(point)
            for d in data:
                longueurs.append(random.random() * (max(d) - min(d)) * (volume ** (1 / len(data))))
            bound = [[(centres[dim] - (longueurs[dim] / 2)), (centres[dim] + (longueurs[dim] / 2))] for dim in
                     range(len(data))]
            nb_tuple = 0
            for y in range(len(data[0])):
                point = [d[y] for d in data]
                if est_inclus(point, bound):
                    nb_tuple += 1
            requetes.append((bound, nb_tuple))
    print(len(requetes))
    return requetes


def print_workload(requetes, data=None):
    """
    Affiche sous forme de rectangle les requêtes généré aléatoirement
    :param requetes:
    :return:
    """
    figure = plt.figure()
    axes = plt.axes()
    axes.set_xlim(left=-10, right=10)
    axes.set_ylim(bottom=-10, top=10)
    subplot = figure.add_subplot(111, sharex=axes, sharey=axes)
    for r in requetes:
        r = r[0]
        print(r)
        bound = (r[0][0], r[1][0])
        w = r[0][1] - r[0][0]
        h = r[1][1] - r[1][0]
        subplot.add_patch(patches.Rectangle(bound, w, h, linewidth=1, fill=False))
    if data is not None:
        plt.scatter(data[0], data[1])
    plt.plot()
    plt.show()