import pickle

path = "./st_histo_test"
f = open(path, "rb")
histogramme = pickle.load(f)
f.close()

print(histogramme.estimer(histogramme.bound, histogramme.dim_name), histogramme.nb_tot_tuple())
