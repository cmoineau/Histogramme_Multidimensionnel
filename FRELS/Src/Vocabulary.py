#!/usr/bin/python

import sys
import os
from collections import OrderedDict


class Modality(object):

    def __init__(self, attribute, modname):
        self.attribute = attribute
        self.modname = modname
        self.fullname = None

    def getName(self):
        return self.modname

    def getFullName(self):
        if self.fullname is None:
            self.fullname = "%s.%s"%(self.attribute.getName(), self.modname)
        return self.fullname

    def getAttribute(self):
        return self.attribute

    def getMu(self, *args):
        raise Exception("This class is abstract")

    def getMinMu(self, *args):
        raise Exception("This class is abstract")

    def getMaxMu(self, *args):
        raise Exception("This class is abstract")

    def getIntersection(self, *args):
        raise Exception("This class is abstract")

    def getDerivedPredicate(self, alpha=0):
        raise Exception("This class is abstract")

    def toString(self):
        return self.modname

    def __repr__(self):
        return self.__str__()


class TrapeziumModality(Modality):
    "This class represents a modality of an attribute, ex: 'young' for attribute 'age' represented by a trapezium"

    def isTrapeziumModality(self):
        return True
    def isEnumModality(self):
        return False

    def __init__(self, attribute, modname, minSupport, minCore, maxCore, maxSupport):
        Modality.__init__(self, attribute, modname)
        self.minSupport = minSupport
        self.minCore = minCore
        self.maxCore = maxCore
        self.maxSupport = maxSupport

    def getDerivedPredicate(self, alpha=0):
        columname = self.getAttribute().getName()
        mi = self.minSupport + (self.minCore - self.minSupport) * alpha
        ma = self.maxSupport - (self.maxSupport - self.maxCore) * alpha
        if mi < ma:
            return "(%f <= %s AND %s <= %f)"%(mi,columname,columname,ma)
        else:
            return "(%s <= %f OR %s >= %f)"%(columname,ma,columname,mi)

    def getMu(self, v):
        "returns the satisfaction degree of v to this modality"
        ret = 0.0
        if v is None:
            ret = 0.0
        else:
            v = float(v)
            # est-ce que la modalité est inversée ?
            if self.maxSupport < self.minSupport:
                if v >= self.minCore or v <= self.maxCore:
                    # in the core
                    ret = 1.0
                elif v >= self.minSupport:
                    # left to the core
                    ret = 1.0 - ((self.minCore - v) / (self.minCore - self.minSupport))
                elif v <= self.maxSupport:
                    # right to the core
                    ret =  (self.maxSupport - v) / (self.maxSupport - self.maxCore)
                # out of the support
                else:
                    ret = 0.0
            else:
                # modalité normale
                if v > self.maxSupport or v < self.minSupport:
                    # out of the support
                    ret = 0.0
                elif v < self.minCore:
                    # left to the core
                    ret = (v - self.minSupport) / (self.minCore - self.minSupport)
                elif v > self.maxCore:
                    # right to the core
                    ret = (self.maxSupport - v) / (self.maxSupport - self.maxCore)
                # in the core
                else:
                    ret = 1.0
        return ret


    def getMinMu(self, lo, hi, verbose=0):
        "returns minimal value of µ along the interval [lo, hi["
        # obligation : lo <= hi
        if hi < lo:
            # échanger les valeurs
            lo, hi = hi, lo
        # est-ce que la modalité est inversée ?
        if self.maxSupport < self.minSupport:
            ## modalité inversée
            # [lo,hi[ est entièrement dans le noyau
            if lo > self.minCore or hi < self.maxCore:
                return 1.0
            # [lo,hi[ encadrent la zone nulle entre les deux supports
            if lo <= self.maxSupport and hi >= self.minSupport:
                return 0.0
            # [lo, hi[ est entièrement dans le support
            return min(self.getMu(lo), self.getMu(hi))
        else:
            ## modalité normale
            # [lo,hi[ est partiellement avant ou partiellement après le support
            if lo <= self.minSupport or hi >= self.maxSupport:
                return 0.0
            # [lo, hi[ est entièrement dans le support
            return min(self.getMu(lo), self.getMu(hi))


    def getMaxMu(self, lo, hi, verbose=0):
        "returns maximal value of µ along the interval [lo, hi["
        # obligation : lo <= hi
        if hi < lo:
            # échanger les valeurs
            lo, hi = hi, lo
        # est-ce que la modalité est inversée ?
        if self.maxSupport < self.minSupport:
            ## modalité inversée
            # [lo,hi[ est entièrement dans le noyau
            if lo > self.minCore or hi < self.maxCore:
                return 1.0
            # cas intermédiaire
            return max(self.getMu(lo), self.getMu(hi))
        else:
            ## modalité normale
            # [lo,hi[ est entièrement hors du support (aucune intersection)
            if hi <= self.minSupport or lo >= self.maxSupport:
                return 0.0
            # [lo,hi[ encadrent le noyau
            if lo <= self.minCore and hi >= self.maxCore:
                return 1.0
            # cas intermédiaire
            return max(self.getMu(lo), self.getMu(hi))
        

    def getIntersection(self, lo, hi, verbose=0):
        "returns the intersection between self and interval [lo, hi[ relative to this interval"
        if lo == None: lo = -1e300
        if hi == None: hi = +1e300
        if hi <= lo: return 0.0
        surface = 0.0
        # est-ce que la modalité est inversée ?
        if self.maxSupport < self.minSupport:
            # compter la zone ]-inf, maxCore]
            l = min(lo, self.maxCore)
            h = min(hi, self.maxCore)
            if l < h:
                k = 1.0
                surface += k * (h-l)
            # compter la zone ]maxCore, maxSupport[
            l = max(lo, self.maxCore)
            h = min(hi, self.maxSupport)
            if l < h:
                mul = self.getMu(l)
                muh = self.getMu(h)
                k = muh + 0.5*(mul-muh)
                surface += k * (h-l)
            # compter la zone ]minSupport, minCore[
            l = max(lo, self.minSupport)
            h = min(hi, self.minCore)
            if l < h:
                mul = self.getMu(l)
                muh = self.getMu(h)
                k = mul + 0.5*(muh-mul)
                surface += k * (h-l)
            # compter la zone [minCore, +inf[
            l = max(lo, self.minCore)
            h = max(hi, self.minCore)
            if l < h:
                k = 1.0
                surface += k * (h-l)
        else:
            # compter la zone ]minSupport, minCore[
            l = max(lo, self.minSupport)
            h = min(hi, self.minCore)
            if l < h:
                mul = self.getMu(l)
                muh = self.getMu(h)
                k = mul + 0.5*(muh-mul)
                surface += k * (h-l)
            # compter la zone [minCore, maxCore]
            l = max(lo, self.minCore)
            h = min(hi, self.maxCore)
            if l < h:
                k = 1.0
                surface += k * (h-l)
            # compter la zone ]maxCore, maxSupport[
            l = max(lo, self.maxCore)
            h = min(hi, self.maxSupport)
            if l < h:
                mul = self.getMu(l)
                muh = self.getMu(h)
                k = muh + 0.5*(mul-muh)
                surface += k * (h-l)
        # résultat final
        result = surface / (hi - lo)
        if verbose:
            print(self.modname, lo, hi, "=>", result)
        return result

    def getMinAlphaCut(self, alpha):
        "returns the lower bound of alpha-cut"
        return (self.minCore - self.minSupport)*alpha + self.minSupport

    def getMaxAlphaCut(self, alpha):
        "returns the upper bound of alpha-cut"
        return (self.maxCore - self.maxSupport)*alpha + self.maxSupport

    def strDomain(self):
        return "]%.1f,[%.1f,%.1f],%.1f["%(self.minSupport, self.minCore, self.maxCore, self.maxSupport)

    def __str__(self):
        return "Modality %s ]%.1f,[%.1f,%.1f],%.1f["%(self.getFullName(), self.minSupport, self.minCore, self.maxCore, self.maxSupport)

    def __repr__(self):
        return self.__str__()



class EnumModality(Modality):
    """
    This class represents a modality of an attribute, ex: 'reliable' for attribute 'carBrands',
    represented by a enumeration of weighted values.
    """

    def isTrapeziumModality(self):
        return False
    def isEnumModality(self):
        return True

    def __init__(self, attribute, modname, enumeration):
        "fournir un dictionnaire {valeur:degré}"
        Modality.__init__(self, attribute, modname)
        self.enumeration = enumeration

    def getDerivedPredicate(self, alpha=0):
        columname = self.getAttribute().getName()
        # liste de paires (valeur catégorielle, degré mu)
        pairs = map(lambda k: (k, self.enumeration.get(k)), self.enumeration)
        # liste des paires ayant mu supérieur ou égal à alpha
        pairs = filter(lambda k_mu: k_mu[1] >= alpha, pairs)
        # mise en forme des valeurs catégorielles pour SQL
        pairs = map(lambda k_mu: ("'"+(k_mu[0].replace("'","''"))+"'", k_mu[1]), pairs)
        # construction de la condition SQL
        values = ','.join(map(lambda e_mu: e_mu[0], pairs))
        return "(%s IN (%s))"%(columname, values)

    def getMu(self, v):
        "returns the satisfaction degree of v to this modality"
        v = str(v).strip()
        return self.enumeration.get(v, 0.0)

    def __str__(self):
        s = str(self.enumeration).replace(': ', '/')
        if len(s) > 40:
            s = s[:40]+"...}"
        return "Modality %s %s"%(self.getFullName(), s)

    def __repr__(self):
        return self.__str__()


## tests de cette classe
#if __name__ == "__main__":
#    m1 = TrapeziumModality("weekend", 5,5,7,7)
#    print m1
#    print m1.getMu(7)


class Attribute(object):
    "This class represents the partition of an attribute with several modalities, ex: 'age' = { 'young', 'medium', 'old' }"

    def __init__(self, attname):
        "constructor"
        self.attname = attname
        self.modalities = OrderedDict()

    def getModNames(self):
        return list(self.modalities.keys())

    def isTrapeziumPartition(self):
        return all(m.isTrapeziumModality() for m in self.modalities.values())
    def isEnumPartition(self):
        return all(m.isEnumModality() for m in self.modalities.values())

    def addTrapeziumModality(self, modname, minSupport, minCore, maxCore, maxSupport):
        "add a trapezium modality to this partition"
        if modname in self.modalities:
            raise Exception("Partition %s: already defined modality %s"%(self.attname, modname))
        self.modalities[modname] = TrapeziumModality(self, modname, minSupport, minCore, maxCore, maxSupport)

    def addEnumModality(self, modname, enumeration):
        "add a enumeration modality to this partition"
        if modname in self.modalities:
            raise Exception("Partition %s: already defined modality %s"%(self.attname, modname))
        self.modalities[modname] = EnumModality(self, modname, enumeration)

    def getName(self):
        "returns the name of this partition, its attribute identifier"
        return self.attname

    def getModalities(self):
        "returns an iterator on its modalities"
        return list(self.modalities.values())

    def getLabels(self):
        return list(self.modalities.keys())

    def getNbModalities(self):
        return len(self.modalitites)

    def getModality(self, modname):
        "return the specified modality, exception if absent"
        return self.modalities[modname]

    def __str__(self):
        return "Attribute %s:\n\t\t"%self.attname + "\n\t\t".join(map(lambda mn: str(self.modalities[mn]), self.modalities))

    def __repr__(self):
        return self.__str__()



class Vocabulary(object):
    "This class represents a fuzzy vocabulary"

    def __init__(self, filename):
        "reads a CSV file whose format is : attname,modname,minSupport,minCore,maxCore,maxSupport"
        # dictionary of the partitions
        self.attributes = OrderedDict()

        with open(filename, 'r') as source:
            for line in source:
                line = line.strip()
                if line == "" or line[0] == "#": continue
                words = line.split(',')
                if len(words) == 6:
                    # modalité de type trapèze
                    attname,modname,minSupport,minCore,maxCore,maxSupport = words
                    # update existing partition or create new one if missing
                    attribute = self.attributes.setdefault(attname, Attribute(attname))
                    attribute.addTrapeziumModality(modname, float(minSupport), float(minCore), float(maxCore), float(maxSupport))
                elif len(words) == 3:
                    # modalité de type énuméré
                    attname,modname,enumeration = words
                    # analyser l'enumération en tant que dictionnaire {valeur:degré}
                    enumeration = enumeration.split(';')
                    enumeration = map(lambda vw: (vw.split(':')[0], float(vw.split(':')[1])), enumeration)
                    enumeration = dict(enumeration)
                    # update existing partition or create new one if missing
                    attribute = self.attributes.setdefault(attname, Attribute(attname))
                    attribute.addEnumModality(modname, enumeration)
                else:
                    print(len(words))
                    raise Exception("%s: bad format line %s"%(filename, line))

    def getAttributeNames(self):
        return list(self.attributes.keys())

    def getNbAttributes(self):
        return len(self.attributes)

    def getAttributes(self):
        return list(self.attributes.values())

    def getDescribedAttributes(self):
        return list(self.attributes.keys())

    def getAttribute(self, attname):
        return self.attributes[attname]

    def __str__(self):
        return "Vocabulary:\n\t" + "\n\t".join(map(str, self.attributes.values()))

    def __repr__(self):
        return self.__str__()


# test du logiciel
if __name__ == '__main__':
    ## chargement du vocabulaire
    vocFile = '../Data/FlightsVoc.txt'
    voc = Vocabulary(vocFile)
    #print(voc)

    # test de getMinMu et getMaxMu
    att = Attribute("test")
    mnrm = TrapeziumModality(att, "mnrm", 0, 10, 20, 30)
    for lo,hi in [(-5,0), (-5, 5), (2, 8), (5, 15), (15, 25), (15, 35), (-5, 35), (25, 35)]:
        print("%s: entre %g et %g : min µ=%g max µ=%g"%(mnrm,lo,hi,mnrm.getMinMu(lo,hi), mnrm.getMaxMu(lo,hi)))
    minv = TrapeziumModality(att, "minv", 20, 22, 5, 7)
    for lo,hi in [(1, 3), (4, 6), (6, 8), (12, 16), (18, 20), (19, 21), (20, 22), (21, 23), (23, 24), (4, 21), (6, 21)]:
        print("%s: entre %g et %g : min µ=%g max µ=%g"%(minv,lo,hi,minv.getMinMu(lo,hi), minv.getMaxMu(lo,hi)))

    
