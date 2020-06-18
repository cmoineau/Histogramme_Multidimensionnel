from pickle import load
from MHIST import Mhist
from GENHIST import Genhist
from STHOLES import Stholes, Workload

dic_histo = {"mhist": 0, "genhist": 1, "stholes": 2}


class Histogramme_wrapper(object):
    def __init__(self):
        self.histogramme = None
        self.type_histogramme = None
        self.path = None

    def load_histogramme(self, path):
        with open(path, "rb") as f:
            self.histogramme = load(f)
            terminaison = path.split("/")[-1].split(".")[-1]
            self.type_histogramme = dic_histo[terminaison]
            self.path = path

    def create_MHIST(self, data, attributes_name, path, max_classes=500):
        histo = Mhist.Mhist(data, attributes_name, max_classes)
        histo.save(path+".mhist")

    def create_GENHIST(self, data, attributes_name, path, b=50, xi=10):
        alpha = (1 / 2) ** (1 / len(data))
        histo = Genhist.Genhist(data, attributes_name, b, xi, alpha)
        histo.save(path+".genhist")

    def create_STHoles(self, attributes_name, path, max_classes=500):
        histo = Stholes.Stholes(attributes_name, max_classes)
        histo.save(path+".stholes")

    def estimer(self, attributs, zones):
        if self.histogramme is None:
            raise ValueError("Il faut d'abord charger un histogramme !")
        return self.histogramme.estimer(attributs, zones)

    def train_STHoles(self, data, nb_queries, volume=0.01):
        if self.type_histogramme != 2:
            raise ValueError("Il faut charger un histogramme STHoles pour l'entraîner !")
        workload = Workload.create_workload_full(data, volume, nb_queries)
        self.histogramme.BuildAndRefine(workload)
        self.histogramme.save(self.path)

    def show_hist(self):
        if self.histogramme is None:
            raise ValueError("Il faut d'abord charger un histogramme !")
        self.histogramme.print()
