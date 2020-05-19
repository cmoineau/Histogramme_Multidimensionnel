import pickle

path = "./st_histo_test"
f = open(path, "rb")
histogramme = pickle.load(f)
f.close()

print(histogramme.estimer(histogramme.intervalles, histogramme.attributes_name), histogramme.nb_tot_tuple())
