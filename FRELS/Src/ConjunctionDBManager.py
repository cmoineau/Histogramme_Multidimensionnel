#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Ce module fait les calculs de cardinalité relative sur des conjonctions de modalités
# Ses méthodes principales sont :
#   - getTuplesSelectedByConjunction(self, modalities)
#       retourne un curseur sur les tuples des supports des modalités
#   - getEstimatedConjunctionCardinality(self, vocabulary, columnnames, modalitynames)
#       retourne la cardinalité relative estimée de la conjonction des columnnames.modalitynames
#   - getRealConjunctionCardinality(self, vocabulary, columnnames, modalitynames)
#       retourne la cardinalité relative réelle de la conjonction des columnnames.modalitynames


from DBManager import *
from Vocabulary import *
import psycopg2.extras
import operator

# reduce n'existe plus en standard dans python3, mais peut-être importée
import sys
if sys.version_info >= (3, 0):
    from functools import reduce


class ConjunctionDBManager(DBManager):

    def getConjunctionString(self, modalities):
        return ' AND '.join(map(lambda modality: modality.getFullName(), modalities))


    def getTuplesSelectedByConjunction(self, modalities, cursor_factory=None):
        """
        Get a dictionnary cursor to the selected tuples
        modalities is an array of Modality instances
        cursor_factory is psycopg2.extras.RealDictCursor to get dictionaries for rows, or psycopg2.extras.NamedTupleCursor for a named tuple
        NB: dans les dictionnaires résultants, les clés sont en minuscule
        """
        # préparer la requête SQL permettant de récupérer les tuples concernés
       
        if len(modalities) == 0:
            proj = '*'
            where = ''
        else:
            proj = ', '.join(map(lambda mod: mod.getAttribute().getName(), modalities))
            where = " WHERE %s"%\
                " AND ".join(map(lambda mod: mod.getDerivedPredicate(), modalities))
        querystring = "SELECT %s FROM %s%s"%(proj, self.tablename, where)
        return querystring
        # exécuter la requête afin de récupérer un curseur de dictionnaires
        query = self.connection.cursor(cursor_factory=cursor_factory)
        query.execute(querystring)
        return query


    def getSampleTuplesSelectedByConjunction(self, modalities, percent):
        """
        Get a dictionnary cursor to the selected tuples
        modalities is an array of Modality instances
        percent is a float indicating sample size in %
        NB: dans les dictionnaires résultants, les clés sont en minuscule
        """
        # préparer la requête SQL permettant de récupérer les tuples concernés
        if len(modalities) == 0:
            proj = '*'
            where = ''
        else:
            proj = ', '.join(map(lambda mod: mod.getAttribute().getName(), modalities))
            where = " WHERE %s"%\
                " AND ".join(map(lambda mod: mod.getDerivedPredicate(), modalities))
        querystring = "SELECT %s FROM %s TABLESAMPLE SYSTEM(%f)%s"%(proj, self.tablename, percent, where)
        # exécuter la requête afin de récupérer un curseur de dictionnaires
        query = self.connection.cursor()
        query.execute(querystring)
        return query


    def getSampleCountDistinctSelectedByConjunction(self, modalities, percent):
        """
        Get a dictionnary cursor to the selected tuples
        modalities is an array of Modality instances
        percent is a float indicating sample size in %
        NB: dans les dictionnaires résultants, les clés sont en minuscule
        """
        # TODO évaluer le treillis des distincts sur les mêmes tuples : gain de temps du tirage et meilleur test d'indépendance
        # préparer la requête SQL permettant de récupérer les tuples concernés
        proj = ', '.join(map(lambda mod: mod.getAttribute().getName(), modalities))
        where = " WHERE %s"%\
                ' AND '.join(map(lambda mod: mod.getDerivedPredicate(), modalities))
        querystring = "SELECT COUNT(DISTINCT(%s)) FROM %s TABLESAMPLE SYSTEM(%f)%s"%(proj, self.tablename, percent, where)
        #plus lent : querystring = "SELECT COUNT(*) FROM (SELECT DISTINCT(%s) FROM %s TABLESAMPLE SYSTEM(%f)%s) AS tmp"%(proj, self.tablename, percent, where)
        # exécuter la requête
        with self.connection.cursor() as query:
            query.execute(querystring)
            return query.fetchone()[0]

    def getEstimatedConjunctionCardinality(self, vocabulary, columnnames, modalitynames):
        # liste des cardinalités relatives
        indivEstimates = []
        for columnname, modalityname in zip(columnnames, modalitynames):
            # modalité portant le nom demandé
            attribute = vocabulary.getAttribute(columnname)
            modality = attribute.getModality(modalityname)
            # cardinalité relative
            indivEstimates.append(
                self.getEstimatedCardinality(vocabulary, columnname, modalityname)[0])
        # combiner les cardinalités relatives de toutes ces modalités
        return self._combineEstimates(indivEstimates)


    def _combineEstimates(self, estimates):
        return reduce(operator.mul, estimates)


    def getEstimatedConjunctionCardinalityMods(self, vocabulary, modalities, distincts=None):
        """
        estimates the relative cardinality of a conjunction of modalities
        this is the product of the estimations on the individual modalities if distincts is absent
        this is a bayesian approach (Heimel 2009) if distincts is given
        """
        if distincts is None:
            return sum(map(
                lambda modality: self.getEstimatedCardinalityModality(vocabulary, modality)[0],
                modalities)) / distincts[self.getConjunctionString(modalities)]
        else:
            # CHANTIER profiter des informations sur le nombre de n-uplets distincts pour améliorer l'estimation de la conjonction
            for modality in modalities:
                print("%s : %g"%(modality,float(distincts[modality.getFullName()])/distincts[self.getConjunctionString(modalities)]))
            return sum(map(
                lambda modality: self.getEstimatedCardinalityModality(vocabulary, modality)[0]*distincts[modality.getFullName()],
                modalities)) / distincts[self.getConjunctionString(modalities)]


    def calcSatisfactionDegree(self, vet, atts, mods):
        """
        vocabulary is an instance of the Vocabulary class,
        vet a dict modName=>mu,
        atts a list of attribute names,
        mods a list of modality names
        """
        degs = []
        for att,mod in zip(atts,mods):
            mu = vet[att+"."+mod]
            degs.append(mu)
        muF = self._combineSatisfactionDegrees(degs)
        return muF


    def _combineSatisfactionDegrees(self, mus):
        "opérateur de Zadeh pour effectuer un AND sur les degrés de satisfaction µ"
        #v = reduce(lambda x,y: min(x,y), mus)
        v = min(mus)
        return v


    def calcSatisfactionDegreeFast(self, rwvector, modalities):
        """
        Simplification of calcSatisfactionDegree
        rwvector a dict {modality: µ(modality)},
        modalities a list of modalities
        """
        return min(map(lambda modality: rwvector[modality], modalities))


    def _getRealConjunctionCardinality(self, modalities):
        """
        calcule la cardinalité floue de la conjonction des modalités par un parcours
        intégral des n-uplets sélectionnés par les supports des modalités
        attributes is an array of attribute names
        modalities is an array of Modality instances
        """
        score = 0.0
        query = None
        try:
            query = self.getTuplesSelectedByConjunction(modalities)
            for row in query:
                # opérateur de Zadeh pour calculer le degré de satisfaction de la conjonction
                score += min(map(lambda modality, column: modality.getMu(column), modalities, row))
        finally:
            if query: query.close()
        return score


    def getRealConjunctionCardinality(self, vocabulary, columnnames, modalitynames):
        """
        calcule les cardinalités floues de toutes les modalités de la colonne par un parcours
        des n-uplets sélectionnés par les supports des modalités
        attributes is an array of attribute names
        modalities is an array of Modality instances
        """
        nb_tuples = self.getCount()
        if nb_tuples == 0:
            score = 0
        else:
            # obtenir les objets modality associés aux modalitynames des columnnames
            modalities = list(map(lambda a,m: vocabulary.getAttribute(a).getModality(m),
                             columnnames, modalitynames))
            # calcul des cardinalités par un parcours des n-uplets concernés
            score = self._getRealConjunctionCardinality(modalities)
            score = score / nb_tuples
        return score



# tests simples
if __name__ == "__main__":
    import time

    # charger le vocabulaire
    vocFile = '../Data/FlightsVoc.txt'
    vocabulary = Vocabulary(vocFile)

    # host, database and table 
    host = 'localhost'
    database = 'flights'
    table = 'flights'

    # ouvrir une connexion à la base pour un estimateur
    with ConjunctionDBManager(host, database, table) as manager:

        # on s'intéresse à la conjonction (ArrTime.night AND AirTime.long)
        attributes = ['ArrTime', 'AirTime']
        modalitynames = ['night', 'veryShort']
      
        modalities = map(lambda a,m: vocabulary.getAttribute(a).getModality(m),
                         attributes,
                         modalitynames)
        nomconjonction = manager.getConjunctionString(modalities)
      
        # nombre de valeurs distinctes de la conjonction et de ses composantes
        if False:
            percent = 10
            t_beg = time.time()
            nb_tuples = manager.getCount()
            print("Direct computations on %d tuples"%nb_tuples)
            distincts = {'all': nb_tuples}
            distincts[nomconjonction] = manager.getSampleCountDistinctSelectedByConjunction(modalities, percent)
            print("nombre de valeurs distinctes de (%s) = %d (sur %g%% des tuples)"%(nomconjonction, distincts[nomconjonction], percent))
            for mod in modalities:
                with manager.getTuplesSelectedByConjunction([mod]) as cursor:
                    print("%s : %d"%(mod, cursor.rowcount))
                distincts[mod.getFullName()] = manager.getSampleCountDistinctSelectedByConjunction([mod], percent)
                print("nombre de valeurs distinctes de (%s) = %d (sur %g%% des tuples)"%(mod.getFullName(), distincts[mod.getFullName()], percent))
            t_end = time.time()
            print("Elapsed time = %ss\n"%round(t_end-t_beg, 3))

        # compter les n-uplets satisfaisant la conjonction
        if False:
            t_beg = time.time()
            with manager.getTuplesSelectedByConjunction(modalities) as query:
                print("Il y a %d nuplets satisfaisant %s"%(query.rowcount, nomconjonction))
            t_end = time.time()
            print("Elapsed time = %ss\n"%round(t_end-t_beg, 3))

        # cardinalité relative réelle
        if True:
            t_beg = time.time()
            score = manager.getRealConjunctionCardinality(vocabulary, attributes, modalitynames)
            t_end = time.time()
            print("cardinalité relative réelle de (%s) = %f"%(nomconjonction, score))
            print("Elapsed time = %ss\n"%round(t_end-t_beg, 3))

        # cardinalité relative estimée par un simple produit
        if True:
            t_beg = time.time()
            score = manager.getEstimatedConjunctionCardinality(vocabulary, attributes, modalitynames)
            t_end = time.time()
            print("cardinalité relative estimée de (%s) = %f"%(nomconjonction, score))
            print("Elapsed time = %ss\n"%round(t_end-t_beg, 3))

        # cardinalité relative estimée par une combinaison bayésienne
        if False:
            t_beg = time.time()
            score = manager.getEstimatedConjunctionCardinalityMods(vocabulary, modalities, distincts)
            t_end = time.time()
            print("cardinalité relative estimée de (%s) = %f"%(nomconjonction, score))
            print("Elapsed time = %ss\n"%round(t_end-t_beg, 3))
