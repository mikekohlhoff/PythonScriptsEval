import numpy as np
import numpy.random as rand

def trapz_err(x, y, err, nit=100):
    areas = np.zeros(nit)
    n = len(x)
    for i in xrange(nit):
        rand_y = rand.normal(size=n) * err + y
        areas[i] = np.trapz(x, rand_y)

    return np.mean(areas), np.std(areas)

