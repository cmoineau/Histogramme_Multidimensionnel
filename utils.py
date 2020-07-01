# -*- coding: UTF-8 -*-

from math import sqrt
import random

epsilon = 0.00001  # On a besoin d'un espilon pour faire des tests et éviter les problèmes de virgule flottante


def coef_correlation(tab_attribut):
    '''
    Réalise le calcul du coefficient de corrélation classique et l'affiche
    :param tab_attribut:
    :return:
    '''
    n = 0
    Sx = 0
    Sy = 0
    Sxy = 0
    Sxs = 0
    Sys = 0
    for i in range(len(tab_attribut[0])):
        Sx += tab_attribut[0][i]
        Sy += tab_attribut[1][i]
        Sxs += (tab_attribut[0][i] ** 2)
        Sys += (tab_attribut[1][i] ** 2)
        Sxy += (tab_attribut[1][i] * tab_attribut[0][i])
        n += 1
    Up = (Sxy / n) - (Sx / n) * (Sy / n)  # tab_classe(XY)-tab_classe(X)tab_classe(Y)
    Down = sqrt((Sxs / n) - (Sx / n) ** 2) * sqrt((Sys / n) - (Sy / n) ** 2)  # sigma_x.sigma_y
    return round(float(Up/Down), 3)


def est_inclus(point, bound):
    if len(point) != len(bound):
        raise ValueError("Il faut que les deux objets aient la même dimension !")
    inclus = True
    dim = 0
    while dim < len(bound) and inclus:
        if bound[dim][0] - epsilon <= point[dim] <= bound[dim][1] + epsilon:
            dim += 1
        else:
            inclus = False
    return inclus


def generate_req(nb_req, data_set):
    tab_min_max = [(min(data), max(data)) for data in data_set[1]]
    tab_req = []
    for _ in range(nb_req):
        tab_attribut = []
        tab_bound = []
        while not tab_attribut:  # On vérifie qu'on ait au minimum 1 attribut
            for i in range(len(data_set[0])):
                if random.random() > 0.5 and data_set[0][i] not in tab_attribut:
                    tab_attribut.append(data_set[0][i])
                    centre = random.randrange(int(tab_min_max[i][0]), int(tab_min_max[i][1]), 1)
                    demi_largeur = random.random() * (tab_min_max[i][1] - tab_min_max[i][0]) * 0.1 / 2
                    tab_bound.append([centre - demi_largeur, centre + demi_largeur])
        tab_req.append((tab_attribut, tab_bound))
    return tab_req
