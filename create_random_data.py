"""
:author : Cyril MOINEAU
:creation_date : 12/02/20
:last_change_date : 12/02/20
:description : Un simple script permettant de générer des données aléatoirement pour tester des histogrammes.
"""
from random import gauss, expovariate
import matplotlib.pyplot as plt
path = "./DATA/small_data.txt"


def create_data(path):
    nb_tuple = 10000
    att1 = [round(gauss(0, 1), 1) for i in range(nb_tuple)]
    att2 = [round(gauss(0, 1), 1) for i in range(nb_tuple)]
    att3 = [round(expovariate(2), 1) for i in range(nb_tuple)]

    with open(path, "w") as f:
        for i in range(nb_tuple):
            f.write(str(att1[i]) + ","+str(att2[i]) + "," + str(att3[i]) + "\n")
    print('End !')


create_data(path)