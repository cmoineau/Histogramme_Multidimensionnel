#!/usr/bin/python
# -*- coding: UTF-8 -*-

# This script defines the Quantifier class
# a Quantifier represents a fuzzy quantifier, defined by four bounds

import itertools


class Quantifier(object):

    def __init__(self, label, mins, minc, maxc, maxs):
        """
        Constructor for a fuzzy quantifier defined by 4 bounds (min,max) x (support,core)

        @param label (string)
        @param mins (float or None) min(support)
        @param minc (float or None) min(core)
        @param maxc (float or None) max(core)
        @param maxs (float or None) max(support)
        """
        self.label      = label
        self.minSupport = mins
        self.minCore    = minc
        self.maxCore    = maxc
        self.maxSupport = maxs

    def __repr__(self):
        return self.label


    def getLabel(self):
        return self.label


    def getMu(self, v):
        # cas exceptionnel : bornes minimales à l'infini
        if self.minSupport is None or self.minCore is None:
            if v <= self.maxCore:
                return 1.0
            if v >= self.maxSupport:
                return 0.0
            return (v-self.maxSupport) / (self.maxCore-self.maxSupport)
        # cas exceptionnel : bornes maximales à l'infini
        if self.maxSupport is None or self.maxCore is None:
            if v >= self.minCore:
                return 1.0
            if v <= self.minSupport:
                return 0.0
            return (v-self.minSupport) / (self.minCore-self.minSupport)
        # cas ordinaire d'un trapèze
        ret = 0.0
        if v >= self.minCore and v <= self.maxCore:
            ret = 1.0
        elif v > self.minSupport and v < self.minCore:
            ret = (v-self.minSupport) / (self.minCore-self.minSupport)
        elif v > self.maxCore and v < self.maxSupport:
            ret = (v-self.maxSupport) / (self.maxCore-self.maxSupport)
        return ret



class QuantifierDistribution(object):

    def __init__(self):
        """Constructor for a distribution of quantifiers
        is an array of quantifiers as it is important to keep the ordering"""
        self.quantifiers = []
        self.quantifiers.append(Quantifier("None",        None,   None,   0.0,    0.01))
        self.quantifiers.append(Quantifier("Few",         0,      0.01,   0.05,   0.07))
        self.quantifiers.append(Quantifier("Some",        0.05,   0.07,   0.15,   0.5))
        self.quantifiers.append(Quantifier("Around half", 0.15,   0.5,    0.5,    0.6))
        self.quantifiers.append(Quantifier("Most",        0.5,    0.6,    0.99,   1.0))
        self.quantifiers.append(Quantifier("All",         0.99,   1,      None,   None))


    def nbQuantifiers(self):
        return len(self.quantifiers)

    def getMatchingQuantifiers(self, v, threshold=0.5):
        """
        returns the two best quantifiers for the relative cardinality v
        (strong discretization of the coverage)

        @param v (float) is a relative cardinality
        @return (list of (Quantifier, float)) an ordered list of at most two couples (the quantifier, his satisfaction degree mu)
        """
        # build the list of couples (quantifier, µ_quantifier(v))
        list_quant_mu = map(lambda q: (q, q.getMu(v)), self.quantifiers)
        # keep only the couples where µ > threshold
        list_quant_mu_above_thr = filter(lambda q_mu: q_mu[1] > threshold, list_quant_mu)
        # return the first two elements of this list
        return list(itertools.islice(list_quant_mu_above_thr, 2))


# some easy tests
if __name__ == '__main__':
    qd = QuantifierDistribution()
    # test with several relative cardinalities
    for v in [0.0, 0.004, 0.02, 0.065, 0.1, 0.3, 0.45, 0.78, 0.9, 0.993, 1.0]:
        print("When v=%.3f :"%v)
        for q,mu in qd.getMatchingQuantifiers(v, threshold=0.0):
            print('\tQuantifier "%s" with µ=%.3f'%(q, mu))
        print('')



