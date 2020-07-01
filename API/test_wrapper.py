# -*- coding: UTF-8 -*-

"""
A supprimer, juste un script pour tester l'implémentation du wrapper.
"""
from API import wrapper
w = wrapper.Histogramme_wrapper

def create_test_hist():
    path = "../DATA/small_data.txt"
    att1 = []
    att2 = []
    with open(path, "r") as f:
        for line in f:
            line = line.split(',')
            att1.append(float(line[0]))
            att2.append(float(line[1]))
    data = [att1, att2]
    attributes_name = ("x", "y")
    wrapper = w
    wrapper.creer_MHIST(data, attributes_name, "test")
    wrapper.creer_GENHIST(data, attributes_name, "test")
    wrapper.creer_STHoles(attributes_name, "test")

if __name__ == '__main__':
    w = wrapper.Histogramme_wrapper()
    w.get_attributes()
    w.charger_histogramme("./saved_hist/test.genhist")
    w.get_attributes()