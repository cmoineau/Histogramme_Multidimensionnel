# -*- coding: utf-8 -*-

import numpy as np
from scipy.interpolate import interp1d
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rc('font', family='Arial')
 #np.linspace(0, 10, num=11, endpoint=True)
#nb of conjuncts in the summarizer
x = [1,2,3,4]

#error rat wrt. the real cardinalities
estimate = [0.0015,0.002414,0.004047,0.008047,]
frels=[0.000,0.002227,0.003885,0.00798]

ax = plt.figure().gca()

# = interp1d(x, estimate)
#f2 = interp1d(x, y, kind='cubic')

xnew = np.linspace(0, 300, num=41, endpoint=True)

plt.plot(x, estimate,'r--',linewidth=3.0)#, xnew, f(xnew), '-', xnew, f2(xnew), '--')
plt.plot(x, frels,'b-',linewidth=3.0)#, xnew, f(xnew), '-', xnew, f2(xnew), '--')


ax.xaxis.set_major_locator(MaxNLocator(integer=True))
plt.xlabel(u'Nombre de termes dans les résumeurs', fontsize=18)
plt.ylabel(u"Taux d'erreur", fontsize=18)
plt.grid(True)
plt.show()