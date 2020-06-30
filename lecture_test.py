# -*- coding: UTF-8 -*-

import json
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from statistics import mean, pstdev

# path = './DATA/test_artificial_2D.json'
# path = './DATA/test_flight_2D.json'
# path = './DATA/test_artificial_hyper_2D.json'
# path = './DATA/test_flight_hyper_2D.json'
path = './DATA/test_artificial.json'
# path = './DATA/test_flight.json'
# path = './DATA/test_artificial_hyper.json'
# path = './DATA/test_flight_hyper.json'


i = 1


def plot_hist(figure, tab_err, title=''):
    mu = mean(tab_err)
    sigma = pstdev(tab_err, mu=mu)
    global i
    axes = figure.add_subplot(2, 2, i)
    i+=1
    axes.hist(tab_err, bins=100)
    axes.set_title(title)
    axes.axvline(mu, color='r', linewidth=1)
    axes.axvline(mu - (2*sigma), color='g', linewidth=1)
    axes.axvline(mu + (2*sigma), color='g', linewidth=1)
    axes.legend(handles=[mlines.Line2D([], [], color='red', markersize=15, label="Moyenne empirique"),
                        mlines.Line2D([], [], color='green', markersize=15, label="+/- 2 écart type")])


if __name__ == '__main__':
    with open(path, 'r') as f:
        resultats = json.load(f)
        mhist_err = 0
        genhist_err = 0
        stholes_err = 0
        quotient_norm = 0
        cpt = 0
        t_m_err = []
        g_m_err = []
        s_m_err = []
        a_m_err = []
        for k, v in resultats["Resultat"].items():
            if k != "time" and k != "size":
                reel = v["reel"]["resultat"]
                mhist_err += abs(v["MHIST"]["resultat"] - reel)
                genhist_err += abs(v["GENHIST"]["resultat"] - reel)
                stholes_err += abs(v["STHOLES"]["resultat"] - reel)
                quotient_norm += abs(v["AVI"]["resultat"] - reel)
                t_m_err.append(v["MHIST"]["resultat"] - reel)
                g_m_err.append(v["GENHIST"]["resultat"] - reel)
                s_m_err.append(v["STHOLES"]["resultat"] - reel)
                a_m_err.append(v["AVI"]["resultat"] - reel)
        print('Normalized Absolute Error :', '\n',
              'MHIST :', mhist_err / quotient_norm, '\n',
              'GENHIST :', genhist_err / quotient_norm, '\n',
              'STHOLES :', stholes_err / quotient_norm
              )
        figure = plt.figure(figsize=(10, 10))
        plot_hist(figure, t_m_err, title="MHIST")
        plot_hist(figure, g_m_err, title="GENHIST")
        plot_hist(figure, s_m_err, title="STHoles")
        plot_hist(figure, a_m_err, title="AVI")
        plt.show()
