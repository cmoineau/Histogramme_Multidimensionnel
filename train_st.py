import pickle
import STHOLES.Workload as w
if __name__ == '__main__':

    path = "./test_st.histo"
    f = open(path, "rb")
    histogramme = pickle.load(f)
    f.close()
    path = "./DATA/small_data.txt"
    att1 = []
    att2 = []
    att3 = []
    with open(path, "r") as f:
        for line in f:
            line = line.split(',')
            att1.append(float(line[0]))
            att2.append(float(line[1]))
    tab_attribut = [att1, att2]
    nb_validation_q = 500
    test_workload = w.create_workload(tab_attribut, 0.05, nb_validation_q)
    av_err = 0
    for r in test_workload:
        est = round(histogramme.estimer(r[0], histogramme.attributes_name))
        print('est', est, 'real', r[1])
        av_err += abs(est - r[1])
    print("Average Error :", av_err / nb_validation_q)
