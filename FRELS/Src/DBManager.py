#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Ce module est responsable des requêtes de base sur le moteur SQL pour le
# calcul des cardinalités relatives des modalités d'un attribut sur la base
#
# Mode d'emploi :
#   with DBManager(host='localhost', dbname='flights1996', tablename='flights') as manager:
#       resultat = manager.methode...(...)
#
# ou bien
#   manager = DBManager(host='localhost', dbname='flights1996', tablename='flights')
#   try:
#       manager.open()
#       resultat = manager.methode...(...)
#   finally:
#       manager.close()
#
# Ses méthodes principales sont :
#   - getEstimatedCardinality(self, vocabulary, columnname, modalityname)
#       retourne la cardinalité relative de la modalité estimée par les métadonnées
#   - getRealCardinality(self, vocabulary, columnname, modalityname)
#       retourne la cardinalité relative de la modalité calculée par un parcours
#       intégral des n-uplets du support ou des catégories de la modalité
#
# Les méthodes secondaires (intimement liées au SGBD PostgresQL) sont :
#   - getColumnNullFrac(self, columnname)
#       retourne le nombre estimé par les métadonnées de valeurs nulles dans la colonne
#   - getColumnHistogramNumber(self, columnname)
#       retourne l'histogramme d'une colonne de type nombre, les bornes sont des float
#   - getColumnHistogramString(self, columnname)
#       retourne l'histogramme d'une colonne de type chaîne
#   - getColumnCommonsNumber(self, columnname)
#       retourne les métadonnées "valeurs les plus fréquentes" d'une colonne de type nombre
#       les nombres sont convertis en float
#   - getColumnCommonsString(self, columnname)
#       retourne les métadonnées "valeurs les plus fréquentes" d'une colonne de type chaîne
#   - getCount(self)
#       retourne le nombre de n-uplets de la table, y compris les NULL



import psycopg2

from Vocabulary import *

class DBManager(object):
    """
    Cette classe est chargée de la connexion avec la base de données
    ainsi que des requêtes de base : comptage et estimations de cardinalités sur des
    propriétés atomiques.
    Les instances de DBManager sont attachées à une base et une table.
    """

    class ColumnMetaData(object):
        """
        Cette classe permet de mémoriser les statistiques d'une colonne de la base de données :
        histogramme, valeurs fréquentes et nombre de null
        La création d'une instance entraîne une requête
        """

        def __init__(self, manager, columnname, isNumeric):
            """
            Initialise un objet qui stocke les métadata d'une colonne
            Cet objet est mis en cache dans le DBManager, afin de gagner du temps,
            car il n'y a qu'une seule requête au SGBD pour avoir toutes les informations

            @param manager (DBManager) connexion à la base de données et à la table
            @param columnname (string) nom de la colonne
            @param isNumeric (boolean) True si la colonne contient des nombres
            """
            # obtenir les statistiques sur la colonne
            with manager.connection.cursor() as query:

                # demander toutes les informations en une seule fois
                query.execute("""
                    SELECT null_frac, histogram_bounds, most_common_vals, most_common_freqs
                    FROM pg_stats
                    WHERE schemaname='public' AND tablename='%s' AND attname='%s'"""%
                            (manager.tablename.lower(), columnname.lower()))
                # séparer les réponses
                null_frac, histogram_bounds, most_common_vals, most_common_freqs = query.fetchone()
                # nettoyage et conversion des bornes de l'histogramme
                if histogram_bounds is not None:
                    histogram_bounds = histogram_bounds.lstrip('{').rstrip('}')
                    if isNumeric:
                        histogram_bounds = map(lambda s: float(s.strip()),
                                               histogram_bounds.split(','))
                    else:
                        histogram_bounds = map(lambda s: s.lstrip('"').rstrip('"').strip(),
                                               histogram_bounds.split(','))
                    histogram_bounds = list(histogram_bounds)
                else:
                    histogram_bounds = []
                # nettoyage et conversion des valeurs fréquentes
                if most_common_vals is not None:
                    most_common_vals = most_common_vals.lstrip('{').rstrip('}')
                    if isNumeric:
                        most_common_vals = map(lambda s: float(s.strip()),
                                               most_common_vals.split(','))
                    else:
                        most_common_vals = map(lambda s: s.lstrip('"').rstrip('"').strip(),
                                               most_common_vals.split(','))
                    most_common_vals = list(most_common_vals)
                    most_common_freqs = list(most_common_freqs)
                else:
                    most_common_vals = []
                    most_common_freqs = []
                # mémoriser les informations
                self.manager = manager
                self.columnname = columnname
                self.isNumeric = isNumeric
                self.null_frac = null_frac
                self.histogram = histogram_bounds
                self.most_common_vals = most_common_vals
                self.most_common_freqs = most_common_freqs


        def getNullFrac(self):
            """
            retourne la proportion 0..1 de valeurs nulles dans cette colonne de la table
            @return (float) cardinalité relative des null
            """
            return self.null_frac


        def getHistogram(self):
            """
            retourne la liste des bornes de l'histogramme [b0, b1, b2, ... bN] pour N bins
            NB: il y a une borne de plus que de bins
            @return (list(float)) bornes de l'histogramme
            """
            return self.histogram


        def getMostCommonValues(self):
            """
            retourne la liste des couples (valeur fréquente, fréquence de cette valeur)
            @return (list(float ou string, float)) couples (valeur, fréquence)
            """
            return list(zip(self.most_common_vals, self.most_common_freqs))


        def getBinRelativeCardinality(self):
            """
            calcule le poids de chaque bin de l'histogramme :
            C'est (1 - poids des valeurs nulles - poids des valeurs fréquentes) / nombre de bins

            @return (float) cardinalité relative de chaque bin, 0.0 si pas d'histogramme
            """
            # poids de toutes les valeurs fréquentes
            common_weight = sum(self.most_common_freqs)

            # poids de chaque bin de l'histogramme : 1-somme des fréq. des valeurs fréquentes-poids des null
            if self.histogram != None:
                # nombre de bins = 1 de moins que les bornes
                nb_bins = len(self.histogram)-1
                sigma_h = (1.0 - common_weight - self.null_frac) / nb_bins
            else:
                nb_bins = 0
                sigma_h = 0.0

            # résultat
            return sigma_h


        def getBins(self):
            """
            retourne un itérateur sur des couples [lo, hi[ qui sont les bins de l'histogramme

            @return (list(float, float)) bins, None si pas d'histogramme
            """
            if self.histogram is None:
                return
            elif len(self.histogram) == 0:
                return
            else:
                lo = self.histogram[0]
                for hi in self.histogram[1:]:
                    loprec = lo
                    lo = hi
                    yield loprec,hi


    def __init__(self, host, dbname, tablename=None):
        self.host = host
        self.dbname = dbname
        self.tablename = tablename
        self.metadatas = dict()
        self.count_real = None
        self.count_fast = None


    def getDBName(self):
        return self.dbname


    def getTableName(self):
        return self.tablename


    # méthodes pour faire: with DBManager(...) as manager:

    def __enter__(self):
        self.open(self.tablename)
        return self

    def __exit__(self, type, value, traceback):
        self.close()


    # méthodes pour faire: manager = DBManager(...) ; manager.open() ; manager.close()

    def open(self, tablename):
        # voir ~/.pgpass et https://docs.postgresql.fr/9.6/libpq-pgpass.html
        # pour configurer le login et mot de passe par défaut
        self.connection = psycopg2.connect(host=self.host, dbname=self.dbname)

    def close(self):
        self.connection.close()


    # méthodes secondaires et principales

    def getCount(self):
        """
        Retourne le nombre de n-uplets de la table, y compris les null

        @param fast (boolean) estimer le nombre à l'aide des métadonnées, sinon par une requête directe
        @return (int) nombre total de n-uplets dans la table incluant les null
        """
        # la meilleure valeur est-elle déjà connue ?
        if self.count_real is not None:
            return self.count_real
        # if fast:
        #     # a-t-on déjà fait le calcul ?
        #     if self.count_fast is not None:
        #         return self.count_fast
        #     # demander le nombre aux métadonnées
        #     with self.connection.cursor() as query:
        #         # comptage des n-uplets par une requête sur les métadonnées
        #         query.execute("""
        #             SELECT n_live_tup
        #             FROM pg_stat_user_tables
        #             WHERE schemaname='public' AND relname='%s'"""%self.tablename)
        #         self.count_fast = int(query.fetchone()[0])
        #     return self.count_fast
        # else:
        # comptage des n-uplets par une requête directe
        with self.connection.cursor() as query:
            query.execute("SELECT COUNT(*) FROM %s"%self.tablename)
            self.count_real = int(query.fetchone()[0])
        return self.count_real

    def getCountAttribute(self, columnname):
        """
        Retourne le nombre de n-uplets de la table, sans les null

        @return (int) nombre total de n-uplets dans la table incluant les null
        """
        if self.count is None:
            with self.connection.cursor() as query:
                # comptage des n-uplets
                query.execute("SELECT COUNT(*) FROM %s WHERE %s IS NOT NULL"%(self.tablename,columnname))
                self.count = int(query.fetchone()[0])
        return self.count


    def getColumnNullFrac(self, columnname, isNumeric):
        """
        Retourne le nombre relatif estimé de valeurs NULL de la colonne.
        C'est une proportion 0..1 du nombre total de n-uplets

        @param columnname (string) nom de la colonne concernée
        @param isNumeric (boolean) True si la colonne contient des nombres
        @return (float) estimation du nombre de valeurs nulles dans la colonne
        """
        metadata = self.metadatas.get(columnname)
        if metadata is None:
            metadata = DBManager.ColumnMetaData(self, columnname, isNumeric)
            self.metadatas[columnname] = metadata
        return metadata.getNullFrac()


    def getColumnHistogram(self, columnname, isNumeric):
        """
        Retourne l'histogramme de la colonne, c'est la liste des bornes
        Note: dans le cas de valeurs entières ou chaînes, certaines bornes peuvent être dupliquées

        @param columnname (string) nom de la colonne concernée
        @param isNumeric (boolean) True si la colonne contient des nombres
        @return (list(float ou string)) les bornes de l'histogramme
        """
        metadata = self.metadatas.get(columnname)
        if metadata is None:
            metadata = DBManager.ColumnMetaData(self, columnname, isNumeric)
            self.metadatas[columnname] = metadata
        return metadata.getHistogram()


    def getMostCommonValues(self, columnname, isNumeric):
        """
        Retourne la liste des valeurs les plus fréquentes de la colonne
        associées à leur cardinalité relative à tous les n-uplets (en comptant les null)

        @param columnname (string) nom de la colonne concernée
        @param isNumeric (boolean) True si la colonne contient des nombres
        @return (list(float ou string, float)) la liste des couples (valeur, fréquence)
        """
        metadata = self.metadatas.get(columnname)
        if metadata is None:
            metadata = DBManager.ColumnMetaData(self, columnname, isNumeric)
            self.metadatas[columnname] = metadata
        return metadata.getMostCommonValues()


    def getBinRelativeCardinality(self, columnname, isNumeric):
        """
        calcule le poids de chaque bin de l'histogramme de la colonne indiquée
        C'est (1 - poids des valeurs nulles - poids des valeurs fréquentes) / nombre de bins

        @param columnname (string) nom de la colonne concernée
        @param isNumeric (boolean) True si la colonne contient des nombres
        @return (float) cardinalité relative de chaque bin, 0.0 si pas d'histogramme
        """
        metadata = self.metadatas.get(columnname)
        if metadata is None:
            metadata = DBManager.ColumnMetaData(self, columnname, isNumeric)
            self.metadatas[columnname] = metadata
        return metadata.getBinRelativeCardinality()


    def getBins(self, columnname, isNumeric):
        """
        retourne un itérateur sur des couples [lo, hi[ qui sont les bins de l'histogramme

        @param columnname (string) nom de la colonne concernée
        @param isNumeric (boolean) True si la colonne contient des nombres
        @return (list(float, float)) bins, None si pas d'histogramme
        """
        metadata = self.metadatas.get(columnname)
        if metadata is None:
            metadata = DBManager.ColumnMetaData(self, columnname, isNumeric)
            self.metadatas[columnname] = metadata
        return metadata.getBins()


    def _getEstimatedCardinalityNumber(self, vocabulary, columnname, modalityname, debug=False):
        """
        Calcule l'estimation de la modalité d'une colonne de type nombre (trapèze)
        retourne le triplet sigma, sigma_inf, sigma_sup

        @param vocabulary (Vocabulary) vocabulaire
        @param columnname (string) nom de la colonne concernée = attribut flou
        @param modalityname (string) nom de la modalité voulue
        @return (sigma, sigma_inf, sigma_sup) cardinalité relative, bornes d'incertitude inf et sup
        """
        # nombre estimé de valeurs nulles pour cette colonne
        null_frac = self.getColumnNullFrac(columnname, True)
        if debug: print("%.3f%% valeurs nulles"%(null_frac*100.0))

        # récupérer l'histogramme de la colonne
        histogram = self.getColumnHistogram(columnname, True)

        # récupérer les valeurs fréquentes et leur fréquence
        common_values = self.getMostCommonValues(columnname, True)
        if common_values != None:
            common_weight = sum(map(lambda val_freq: val_freq[1], common_values))
            if debug: print("%d common values, weight=%.3f : %s"%(
                len(common_values),common_weight,
                sorted(map(lambda val_freq: val_freq[0], common_values))))
        else:
            common_weight = 0.0
            if debug: print("No common values")

        # poids de chaque bin de l'histogramme : 1-somme des fréq. des valeurs fréquentes-poids des null
        if histogram != None:
            nb_bins = len(histogram)-1
            sigma_h = 1.0 / nb_bins * (1.0 - common_weight - null_frac)
            if debug: print("Histogram with %d bins, weight = %.3f : %s"%(nb_bins,sigma_h, histogram))
        else:
            nb_bins = 0
            sigma_h = 0.0
            if debug: print("No histogram")

        # modalité portant le nom demandé
        partition = vocabulary.getAttribute(columnname)
        modality = partition.getModality(modalityname)

        # calculer la cardinalité relative de la modalité
        sigma = 0.0
        sigma_sup = 0.0
        sigma_inf = 0.0

        # calculer l'impact de l'histogramme
        if histogram:
            lo = histogram[0]
            for hi in histogram[1:]:
                # de combien l'boundary [lo,hi[ est-il dans la modalité ?
                if lo == hi:
                    # cas particulier d'un boundary [lo,lo[ pour une colonne entière = sorte de valeur fréquente
                    mu = modality.getMu(lo)
                else:
                    mu = modality.getIntersection(lo, hi)
                # µ(lo) et µ(hi) encadrant µ
                mu_lo = modality.getMinMu(lo, hi)
                mu_hi = modality.getMaxMu(lo, hi)
                # poids du bin et bornes du poids
                h = sigma_h * mu
                h_inf = sigma_h * min(mu_lo, mu_hi)
                h_sup = sigma_h * max(mu_lo, mu_hi)
                # cumul sur les sigma
                sigma += h
                sigma_inf += h_inf
                sigma_sup += h_sup
                # mise au point
                if debug: print(u"[%s, %s[ => µ = %.3f => h = %.6f, h- = %.6f, h+ = %.6f"%(lo,hi,mu,h,h_inf,h_sup))
                # passage au bin suivant
                lo = hi
        if debug: print(u"σ = %g avec σ- = %g, σ+ = %g"%(sigma, sigma_inf, sigma_sup))
        if common_values:
            # prendre en compte les valeurs fréquentes qui sont hors de l'histogramme
            for val,freq in common_values:
                mu = modality.getMu(val)
                if mu > 0.0:
                    h = freq * mu
                    h_inf = h #freq * 0.0
                    h_sup = h #freq * 1.0
                    sigma += h
                    sigma_inf += h_inf
                    sigma_sup += h_sup
                    if debug: print(u"%s pour %.3f => µ = %.3f => h = %.6f, h- = %.6f, h+ = %.6f"%(modality,val,mu,h,h_inf,h_sup))

        # debug: affichage et tests de validité
        if debug: print(u"σ = %g avec σ- = %g, σ+ = %g"%(sigma, sigma_inf, sigma_sup))
        if sigma<0.0 or sigma>1.0: raise Exception("sigma hors plage")
        if sigma_inf<0.0 or sigma_inf>1.0: raise Exception("sigma_inf hors plage")
        if sigma_sup<0.0 or sigma_sup>1.0: raise Exception("sigma_sup hors plage")
        if sigma<sigma_inf or sigma>sigma_sup: raise Exception("bornes sigma_inf et sigma_sup mal calculées")

        # résultat final
        return sigma, sigma_inf, sigma_sup


    def _getEstimatedCardinalityString(self, vocabulary, columnname, modalityname, debug=False):
        """
        Calcule l'estimation de la modalité d'une colonne de type chaîne (énuméré)
        retourne le triplet sigma, sigma_inf, sigma_sup

        @param vocabulary (Vocabulary) vocabulaire
        @param columnname (string) nom de la colonne concernée = attribut flou
        @param modalityname (string) nom de la modalité voulue
        @return (sigma, sigma_inf, sigma_sup) cardinalité relative, bornes d'incertitude inf et sup
        """
        # nombre de valeurs nulles pour cette colonne
        null_frac = self.getColumnNullFrac(columnname, False)
        if debug: print("%.3f%% valeurs nulles"%(null_frac*100.0))

        # récupérer l'histogramme de la colonne
        histogram = self.getColumnHistogram(columnname, False)

        # récupérer les valeurs fréquentes et leur fréquence
        common_values = self.getMostCommonValues(columnname, False)
        if common_values != None:
            common_weight = sum(map(lambda val_freq: val_freq[1], common_values))
            if debug: print("%d common values, weight=%.3f : %s"%(
                len(common_values),common_weight,
                sorted(map(lambda val_freq: val_freq[0], common_values))))
        else:
            if debug: print("No common values")

        # poids de chaque bin de l'histogramme
        if histogram != None:
            nb_bins = len(histogram)-1
            sigma_h = 1.0 / nb_bins * (1.0 - common_weight - null_frac)
            if debug: print("Histogram with %d bins, weight = %.3f : %s"%(nb_bins,sigma_h, histogram))
        else:
            nb_bins = 0
            sigma_h = 0.0
            if debug: print("No histogram")

        # modalité portant le nom demandé
        partition = vocabulary.getAttribute(columnname)
        modality = partition.getModality(modalityname)

        # calculer la cardinalité relative de la modalité
        sigma = 0.0
        sigma_sup = 0.0
        sigma_inf = 0.0

        # calculer l'impact de l'histogramme
        if histogram:
            for val in histogram:
                mu = modality.getMu(val)
                if mu > 0.0:
                    h = sigma_h * mu
                    h_inf = h
                    h_sup = h
                    sigma += h
                    sigma_inf += h_inf
                    sigma_sup += h_sup

        # rajouter les valeurs fréquentes
        if common_values:
            for val,freq in common_values:
                mu = modality.getMu(val)
                if mu > 0.0:
                    h = freq * mu
                    h_inf = h
                    h_sup = h
                    sigma += h
                    sigma_inf += h_inf
                    sigma_sup += h_sup
                    if debug: print(u"%s pour %.3f => µ = %.3f => h = %.6f, h- = %.6f, h+ = %.6f"%(modality,val,mu,h,h_inf,h_sup))

        # test de validité
        if debug: print(u"σ = %g avec σ- = %g, σ+ = %g"%(sigma, sigma_inf, sigma_sup))
        if sigma<0.0 or sigma>1.0: raise Exception("sigma hors plage")
        if sigma_inf<0.0 or sigma_inf>1.0: raise Exception("sigma_inf hors plage")
        if sigma_sup<0.0 or sigma_sup>1.0: raise Exception("sigma_sup hors plage")
        if sigma<sigma_inf or sigma>sigma_sup: raise Exception("bornes sigma_inf et sigma_sup mal calculées")

        # résultat final
        return sigma, sigma_inf, sigma_sup


    def getEstimatedCardinality(self, vocabulary, columnname, modalityname, debug=False):
        """
        Calcule l'estimation de la modalité d'une colonne
        retourne le triplet sigma, sigma_inf, sigma_sup

        @param vocabulary (Vocabulary) vocabulaire
        @param columnname (string) nom de la colonne concernée = attribut flou
        @param modalityname (string) nom de la modalité voulue
        @return (sigma, sigma_inf, sigma_sup) cardinalité relative, bornes d'incertitude inf et sup
        """
        partition = vocabulary.getAttribute(columnname)
        if partition.isTrapeziumPartition():
            return self._getEstimatedCardinalityNumber(vocabulary, columnname, modalityname, debug)
        if partition.isEnumPartition():
            return self._getEstimatedCardinalityString(vocabulary, columnname, modalityname, debug)
        return None


    def getEstimatedCardinalityModality(self, vocabulary, modality, debug=False):
        """
        Calcule l'estimation de la modalité d'une colonne
        retourne le triplet sigma, sigma_inf, sigma_sup

        @param vocabulary (Vocabulary) vocabulaire
        @param modalityname (Modality) modalité voulue
        @return (sigma, sigma_inf, sigma_sup) cardinalité relative, bornes d'incertitude inf et sup
        """
        modalityname = modality.getName()
        partition = modality.getAttribute()
        columnname = partition.getName()
        if modality.isTrapeziumModality():
            return self._getEstimatedCardinalityNumber(vocabulary, columnname, modalityname, debug)
        if modality.isEnumModality():
            return self._getEstimatedCardinalityString(vocabulary, columnname, modalityname, debug)
        return None


    def _getRealCardinalitySupport(self, attribute, modality):
        """
        calcule la cardinalité floue de la modalité par un parcours des n-uplets
        sélectionnés par le support ou les catégories de la modalité
        """
        score = 0.0
        with self.connection.cursor() as query:
            # ajouter une sélection basée sur le prédicat dérivé, afin de limiter le nombre de n-uplets traités
            sql = "SELECT %s FROM %s WHERE %s"%(attribute, self.tablename, modality.getDerivedPredicate())
            query.execute(sql)
            #print("%s => %d tuples"%(querystr,query.rowcount))
            for row in query.fetchall():
                score += modality.getMu(row[0])
        return score


    def getRealCardinality(self, vocabulary, columnname, modalityname):
        """
        calcule les cardinalités floues de la modalité sur la colonne par un parcours des n-uplets
        du support ou des catégories de la modalité
        """
        nb_tuples = self.getCount()
        if nb_tuples == 0:
            print("no tuples")
            return
        attribute = vocabulary.getAttribute(columnname)
        modality = attribute.getModality(modalityname)
        score = self._getRealCardinalitySupport(columnname, modality) / nb_tuples
        return score


    def getRealCardinalityModality(self, vocabulary, modality):
        """
        calcule les cardinalités floues de la modalité sur la colonne par un parcours des n-uplets
        du support ou des catégories de la modalité
        """
        nb_tuples = self.getCount()
        if nb_tuples == 0:
            print("no tuples")
            return
        modalityname = modality.getName()
        partition = modality.getAttribute()
        columnname = partition.getName()
        score = self._getRealCardinalitySupport(columnname, modality) / nb_tuples
        return score

    # def getEquiWidthHistogram(self, tablename, columnname):
    #     """ Returns an equiwidth histogram of the given tablename.columnname 
    #     By default the definition domain is splitted into 100 buckets
    #     """
    #     eqwhisto=[]
    #     nbBuckets = 100
    #     histogram = self.getColumnHistogramFloat(tablename, columnname)
    #     if histogram != None:
    #         nb_bins = len(histogram)
    #         if DEBUG: print "Histogram with %d bins"%nb_bins
    #     else:
    #         if DEBUG: print "No histogram"
    #     # récupérer les valeurs fréquentes et leur fréquence
    #     common_values = self.getColumnCommonsFloat(tablename, columnname)
    #     if common_values != None:
    #         common_weight = sum(map(lambda (intervalle_a_estimer,freq): freq, common_values))
    #         if DEBUG: print len(common_values),"common values"
    #     else:
    #         if DEBUG: print "No common values"
    #     total = 0.0

    #     # estimer le nombre de n-uplets dans chaque modalité de cet attribut
    #     #partition = vocabulary.getPartition(columnname)
    #     #modality = partition.getModality(modalityLabel)

    #     #print modality,':'
    #     subtotal = 0.0
    #     # calculer l'impact de l'histogramme
    #     if histogram:
    #         minS  = None
    #         maxS  = histogram[0]
    #         bucketWidth = (histogram[len(histogram)-1] - histogram[0]) / (nbBuckets - 2)
    #         if DEBUG: print("BucketWidth for %s.%s = %f"%(tablename,columnname,bucketWidth))

    #         for bi in range(nbBuckets):
    #             #Create a Boolean modality
               
    #             m = TrapeziumModality('bucket'+str(bi),minS,minS,maxS,maxS)

    #             if DEBUG:
    #                 if minS is None:
    #                     print("BUCKET [None,%f]"%(maxS))
    #                 else:
    #                     if maxS is None:
    #                         print("BUCKET [%f,None]"%(minS))
    #                     else:
    #                         print("BUCKET [%f,%f]"%(minS,maxS))
                    
    #             lo = None
    #             for hi in histogram:
    #                 # de combien l'boundary [lo,hi[ est-il dans la modalité ?
    #                 if lo == hi:
    #                     # cas particulier d'un boundary [lo,lo[ pour une colonne entière
    #                     inter = m.getIntersection(lo, hi+EPSILON)
    #                 else:
    #                     inter = m.getIntersection(lo, hi)

    #                 if DEBUG and inter > 0:
    #                     if lo is None:
    #                         print("INTERSECTING WITH [None,%f] = %f"%(hi,inter))
    #                     else:
    #                         if hi is None:
    #                             print("INTERSECTING WITH [%f,None]= %f"%(lo,inter))
    #                         else:
    #                             print("INTERSECTING WITH [%f,%f]= %f"%(lo,hi,inter))

    #                 sigmaBucket = inter / nb_bins * (1.0 - common_weight)
    #                 subtotal += inter / nb_bins * (1.0 - common_weight)
    #                 lo = hi
    #             # rajouter les valeurs fréquentes
    #             if common_values:
    #                 for intervalle_a_estimer,freq in common_values:
    #                     if minS is None:
    #                         if intervalle_a_estimer < maxS:
    #                             sigmaBucket += freq
    #                             subtotal +=  freq
    #                     if maxS is None:
    #                         if intervalle_a_estimer >= minS:
    #                             sigmaBucket += freq
    #                             subtotal +=  freq
    #                     if minS is not None and maxS is not None:
    #                         if intervalle_a_estimer >= minS and intervalle_a_estimer < maxS:
    #                             sigmaBucket += freq
    #                             subtotal += freq
    #             yield [maxS,sigmaBucket]
                
    #             minS=maxS
    #             maxS += bucketWidth
    #             if bi == nbBuckets -1:
    #                 maxS = None

    #         if DEBUG:
    #             print("TOTAL SELECTIVITIES %f"%(subtotal))


# tests simples
if __name__ == "__main__":
    # charger le vocabulaire
    vocFile = '../Data/FlightsVoc.txt'
    vocabulary = Vocabulary(vocFile)

    # host, database and table
    host = 'localhost'
    database = 'flights2008' # valeurs possibles : 'flights1996', 'flights2008'
    table = 'flights'

    # connexion à la base
    with DBManager(host, database, table) as manager:

        # nombre de n-uplets
        nb_tuples = manager.getCount()
        print("Direct computations on %d tuples"%nb_tuples)

        def debugCardinality(columnname, modalityname):
            attribute = vocabulary.getAttribute(columnname)
            modality = attribute.getModality(modalityname)
            sigma_estime, sigma_inf, sigma_sup = manager.getEstimatedCardinality(vocabulary, columnname, modalityname, True)
            sigma_direct = manager.getRealCardinality(vocabulary, columnname, modalityname)
            print("%s : dir=%.6f est=%.6f [%.6f,%.6f] (%+.2f%%)"%(
                modality.getFullName(),
                sigma_direct,
                sigma_estime,sigma_inf,sigma_sup,
                (sigma_estime-sigma_direct)/sigma_direct*100.0 if sigma_direct>1e-3 else 0))


        # débogage ArrTime.afternoon ]13.3,[14.0,17.3],18.3[ : dir=0.253070 est=0.254129 [0.245883,0.262616] (+0.42%)
        if False: debugCardinality('ArrTime','afternoon')

        # débogage ArrTime.night : dir=0.063191 est=0.062047 [0.053903,0.070635] (-1.81%)
        if False: debugCardinality('ArrTime','night')

        # débogage AirTime.long : dir=0.004516 est=0.005070 [0.003249,0.006015] (+12.27%) (peu de bins, pas de valeurs fréquentes)
        if False: debugCardinality('AirTime','long')

        # débogage DayOfWeek.end : dir=0.362290 est=0.367100 [0.367100,0.367100] (+1.33%)
        if False: debugCardinality('DayOfWeek','end')

        # débogage Origin.small : dir=0.297528 est=0.300992 [0.300992,0.300992] (+1.16%)
        if False: debugCardinality('Origin','small')

        # débogage Month.spring (que des valeurs fréquentes, pas d'histogramme) : dir=0.165394 est=0.167080 [0.167080,0.167080] (+1.02%)
        if False: debugCardinality('Month','spring')

        # débogage SecurityDelay.short (aucune information estimée)
        if False: debugCardinality('SecurityDelay','none')

        # débogage CarrierDelay.short : dir=0.011766 est=0.011367 [0.011367,0.011367] (-3.40%)
        if False: debugCardinality('CarrierDelay','short')

        # débogage ArrDelay.onTime ]13.3,[14.0,17.3],18.3[ : dir=0.253070 est=0.254129 [0.245883,0.262616] (+0.42%)
        if False: debugCardinality('ArrDelay','onTime')

        # débogage DepTime.night : dir=0.028734 est=0.029255 [0.018855,0.035346] (+1.81%)
        if False: debugCardinality('DepTime','night')

        # comparaison de toutes les modalités de toutes les colonnes du vocabulaire
        if True:
            for columnname in vocabulary.getAttributeNames():
                attribute = vocabulary.getAttribute(columnname)
                # longueur du plus grand nom de modalité, pour aligner l'affichage plus loin
                lngmax = max(map(lambda m: len(m.getFullName()), attribute.getModalities()))
                # afficher le score de toutes les modalités
                somme_sigma_direct = somme_sigma_estime = 0.0
                for modality in attribute.getModalities():
                    modalityname = modality.getName()
                    sigma_estime, sigma_inf, sigma_sup = manager.getEstimatedCardinality(vocabulary, columnname, modalityname)
                    somme_sigma_estime += sigma_estime
                    sigma_direct = manager.getRealCardinality(vocabulary, columnname, modalityname)
                    somme_sigma_direct += sigma_direct
                    print(("%-"+"%d"%lngmax+"s : dir=%.6f est=%.6f [%.6f,%.6f] (%+.2f%%)")%(
                        modality.getFullName(),
                        sigma_direct,
                        sigma_estime,sigma_inf,sigma_sup,
                        ((sigma_estime-sigma_direct)/sigma_direct*100.0 if sigma_direct>1e-3 else 0)))
                print("Sommes : sigma direct = %.6f, sigma estimé = %.6f"%(somme_sigma_direct, somme_sigma_estime))
                print("")
