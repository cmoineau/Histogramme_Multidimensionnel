

class Rewriter(object):

    def __init__(self, vocabulary):
        self.vocabulary = vocabulary


    def rewriteTuple(self, tup):
        re = dict()
        for att in self.vocabulary.getAttributes():
            attN = att.getName()
            value = tup[attN.lower()]
            for mod in att.getModalities():
                modN = mod.getName()
                mu = mod.getMu(value)
                re[attN+"."+modN] = mu
        return re


    def rewriteTupleFast(self, tup):
        re = dict()
        for att in self.vocabulary.getAttributes():
            attN = att.getName().lower()
            value = tup[attN]
            for mod in att.getModalities():
                mu = mod.getMu(value)
                re[mod] = mu
        return re


