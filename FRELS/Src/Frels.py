#!/usr/bin/python
# -*- coding: UTF-8 -*-

import psycopg2
import time
import sys

from Vocabulary import *
from DBManager import *




class Frels:

    def __init__(self, dbm):
        """ Constructor for a FRELS instance"""
        self.dbManager = dbm


    def checkCardinality(self, vocabulary, modality):
        """
        In this version of checkCardinality, one compute the cardinality
        directly in SQL, so it returns the true cardinality.
        It appears to be the fastest method.

        @param vocabulary !unused! (Vocabulary) is an instance of a Vocabulary
        @param modality (Modality) is a modality
        @return (float) improved estimated cardinality
        """
        if not modality.isTrapeziumModality():
            raise Exception("FRELS does not handle discrete fuzzy sets defined over categorical attributes")

        # variables de travail
        relation = self.dbManager.getTableName()
        attribute = modality.getAttribute().attname
        minS,minC,maxC,maxS = modality.minSupport, modality.minCore, modality.maxCore, modality.maxSupport

        # SQL query generation
        sql = "SELECT SUM(mu) FROM (SELECT CASE\n"

        # côté min
        if minS != minC:
            sql += " WHEN %g <= %s AND %s <  %g THEN (%s-(%f))/(%f)\n"%(
                minS, attribute, attribute, minC, attribute, minS, minC-minS)
        
        # core
        #Specific treatment for round domains (e.g. hours)
        #DepTime,night,22.3,23.0,5.3,6.3
        if maxC < minC:
            sql += " WHEN %g <= %s or %s <= %g THEN 1\n"%(minC, attribute, attribute, maxC)         
        else:
            sql += " WHEN %g <= %s AND %s <= %g THEN 1\n"%(minC, attribute, attribute, maxC)

        # côté max
        if maxS != maxC:
            sql += " WHEN %g <  %s AND %s <= %g THEN (%s-(%f))/(%f)\n"%(
                maxC, attribute, attribute, maxS, attribute, maxS, maxC-maxS)

        # autre
        sql += " ELSE 0.0"

        if maxC < minC:
            sql += "END AS mu FROM %s WHERE %s <= %g OR %s >= %g) t"%(
                relation, attribute, maxS, attribute, minS)
        else:
            sql += "END AS mu FROM %s WHERE %g <= %s AND %s <= %g) t"%(
                relation, minS, attribute, attribute, maxS)

        # exécuter la requête
        #print(sql)
        with self.dbManager.connection.cursor() as query:
            query.execute(sql)
            checkCard = float(query.fetchone()[0])

        # normalisation
        if checkCard > 0:
            nbTuples = self.dbManager.getCount()
            checkCard /= nbTuples

        return checkCard



# tests simples
if __name__ == "__main__":
    # Vocabulary
    # vocFile = '../Data/FlightsVoc.txt'
    vocFile = '../Data/flights_numerical.txt'
    vocabulary = Vocabulary(vocFile)

    # host, database and table
    host = 'localhost'
    database = 'flights2008'
    table = 'flights' #_150K'

    # DB connection
    with DBManager(host, database, table) as manager:

        frels = Frels(manager)

        def error(v1, v2):
            "retourne un % d'erreur de v2 par rapport à v1"
            return (v2 - v1)/v1*100

        def runTestModality(modality):
            "lance les comparaisons du calcul de la cardinalité relative par 4 méthodes"
            modalityname = modality.getName()
            partition = modality.getAttribute()
            columnname = partition.getName()
            runTest(columnname, modalityname)

        def runTest(columnname, modalityname):
            "lance les comparaisons du calcul de la cardinalité relative par 4 méthodes"
            # objets correspondant aux noms indiqués
            attribute = vocabulary.getAttribute(columnname)
            modality  = attribute.getModality(modalityname)
            print("**********************************")
            print("%s : %s"%(modality.getFullName(), modality.strDomain()))

            # calcul de la cardinalité réelle
            realCard = None
            if True:
                t_beg = time.time()
                realCard = manager.getRealCardinalityModality(vocabulary, modality)
                t_end = time.time()
                print("REAL CARDINALITY FOR %s.%s = %g"%(columnname,modalityname,realCard))
                print("\tElapsed time = %ss"%round(t_end-t_beg, 3))

            # vérification de la cardinalité, methode 1c : calcul de µ par SQL complet
            if True:
                t_beg = time.time()
                frelsCard = frels.checkCardinality(vocabulary, modality)
                t_end = time.time()
                if realCard is not None:
                    err = "(%.3f%% err)"%error(realCard, frelsCard)
                else:
                    err = ""
                print("FRELS CARDINALITY FOR %s.%s = %g %s"%(columnname,modalityname,frelsCard, err))
                print("\tElapsed time = %ss"%round(t_end-t_beg, 3))

            # estimation de la cardinalité
            if True:
                t_beg = time.time()
                sigma_estime, sigma_inf, sigma_sup = manager.getEstimatedCardinality(vocabulary, columnname, modalityname)
                t_end = time.time()
                if realCard is not None:
                    err = "(%.3f%% err)"%error(realCard, sigma_estime)
                else:
                    err = ""
                print("ESTIMATED CARDINALITY FOR %s.%s = %g %s IN [%g,%g]"%(columnname,modalityname,sigma_estime, err, sigma_inf, sigma_sup))
                print("\tElapsed time = %ss"%round(t_end-t_beg, 3))

            print("**********************************\n")


        # lancer des tests sur certaines modalités
        if True:
            #runTest('ArrDelay', 'onTime')
            #runTest('DayOfWeek', 'weekend')
            #runTest('DepTime', 'night')
            runTest('AirTime', 'medium')
            #runTest('DepTime', 'midday')
            #runTest('ArrTime', 'morning')
            #runTest('ArrTime', 'night')
            #runTest('AirTime', 'long')
            #runTest('AirTime', 'veryLong')
            #runTest('Distance', 'veryLong')
            #runTest('TaxiIn', 'long')
            #runTest('CarrierDelay', 'acceptable')
            #runTest('SecurityDelay', 'acceptable')

        # lancer le test sur toutes les modalités
        if False:
            for attribute in vocabulary.getAttributes():
                # traiter uniquement les attributs numériques
                if attribute.isTrapeziumPartition():
                    for modality in attribute.getModalities():
                        runTestModality(modality)
