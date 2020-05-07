# -*- coding: utf-8 -*-

import numpy as np
from scipy.interpolate import interp1d
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt

 #np.linspace(0, 10, num=11, endpoint=True)
#nb of conjuncts in the summarizer
x = [1,3,5,7]

#computation time 
real = [5500,16500,28500,40000]
estimate = [0.25,0.25,0.25,0.25]
frels=[0.75,1.2,1.5,2.75]

ax = plt.figure().gca()

# = interp1d(x, estimate)
#f2 = interp1d(x, y, kind='cubic')

xnew = np.linspace(0, 300, num=41, endpoint=True)

plt.plot(x, np.log(real),'g:',linewidth=3.0)#, xnew, f(xnew), '-', xnew, f2(xnew), '--')
plt.plot(x, np.log(frels),'b-',linewidth=3.0)#, xnew, f(xnew), '-', xnew, f2(xnew), '--')
plt.plot(x, np.log(estimate),'r--',linewidth=3.0)#, xnew, f(xnew), '-', xnew, f2(xnew), '--')


ax.xaxis.set_major_locator(MaxNLocator(integer=True))
plt.xlabel('Cardinality of the DB (in million)', fontsize=18)
plt.ylabel('Computation time in s. (log. scale)', fontsize=18)
plt.grid(True)
plt.show()