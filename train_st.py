from API import wrapper
import STHOLES.Workload as w
if __name__ == '__main__':
    path = "./DATA/small_data.txt"
    att1 = []
    att2 = []
    att3 = []
    with open(path, "r") as f:
        for line in f:
            line = line.split(',')
            att1.append(float(line[0]))
            att2.append(float(line[1]))
    data = [att1, att2]
    attributes_name = ("x", "y")
    wrapper = wrapper.Histogramme_wrapper()
    # wrapper.create_STHoles(attributes_name, "./here")

    wrapper.load_histogramme("./here.stholes")
    # wrapper.train_STHoles(data, 100)
    print(wrapper.estimer(["x"], [[-1, 1]]))
    # nb_validation_q = 500
    # test_workload = w.create_workload(tab_attribut, 0.05, nb_validation_q)
    # av_err = 0
    # for r in test_workload:
    #     est = round(histogramme.estimer(r[0], histogramme.attributes_name))
    #     print('est', est, 'real', r[1])
    #     av_err += abs(est - r[1])
    # print("Average Error :", av_err / nb_validation_q)
