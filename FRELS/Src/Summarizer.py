#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Ce programme est la classe principale du projet
# Il calcule les résumés linguistiques flous d'un jeu de données


import time
import copy
import itertools
import operator
import psycopg2.extras
import json
import os.path
import getopt
from collections import defaultdict

# for Python2
try:
    xrange
except NameError:
    xrange = range

from ConjunctionDBManager import *
from Quantifier import *
from RewritingVector import *
from Frels import *

# degré de satisfaction minimal pour une conjonction
# a un impact sur les quantificateurs souhaités (au moins ce degré)
LIMIT = 0.001
FRELS_LIMIT=0.01


class Summary(object):

    def __init__(self, universe, quantifier, qualifier, summarizer, truth, cardinality):
        self.universe    = universe
        self.quantifier  = quantifier
        self.qualifier   = qualifier
        self.summarizer  = summarizer
        self.truth       = truth
        self.cardinality = cardinality


    def __str__(self):
        r = "%s %s"%(self.quantifier.getLabel(), self.universe)
        if self.qualifier is not None:
            r += " that are/have "+self.qualifier+" are/have also "
        else:
            r += " are/have "
        r += self.summarizer+" ("+str(self.truth)+") - ("+str(self.cardinality)+")"
        return r


    def getCode(self):
        r = self.quantifier.getLabel() + ";"
        if self.qualifier is not None:
            r += self.qualifier + ";"
        r += self.summarizer
        return r


    def getSummarizer(self):
        return self.summarizer


    def getQuantifier(self):
        return self.quantifier



class Summarizer(ConjunctionDBManager):

    def __init__(self, host, dbname, tablename, vocabulary, quantifiers, mode="real"):
        """ mode may take the values real or estimate"""
        super(Summarizer, self).__init__(host, dbname, tablename)
        self.vocabulary = vocabulary
        self.nbR = 0
        self.mode = mode
        self.quantifiers = quantifiers
        self.summaries = list()
        self.exploredProperties = dict()
        self.nbTuplesScanned = 0


    def generateSummaries(self, attributes, modalities, relcard):
        # quantificateurs pouvant décrire la cardinalité relative
        matching_quantifiers = self.quantifiers.getMatchingQuantifiers(relcard)

        # texte décrivant la conjonction
        summarizer = ' AND '.join(map(lambda att,mod: "%s %s"%(att,mod), attributes,modalities))

        # générer un résumé pour chaque quantificateur
        for quantifier, score in matching_quantifiers:
            summary = Summary(self.tablename, quantifier, None, summarizer, quantifier, relcard)
            #print(summary.getLinguisticStatement())
            self.summaries.append(summary)
            self.nbR += 1


    def generateSummariesModalities(self, modalities, pi_sigma, pi_sigma_inf, pi_sigma_sup):
        # texte décrivant la conjonction
        summarizer = ' AND '.join(
            map(lambda mod: "%s"%(mod.getFullName()), modalities))

        matching_quantifiers = self.quantifiers.getMatchingQuantifiers(pi_sigma)
        for quantifier in matching_quantifiers:

            # générer un résumé pour ce quantificateur
            s = Summary(self.tablename, quantifier[0], None, summarizer, quantifier[0], pi_sigma)
#               print(s)
            self.summaries.append(s)
            self.nbR += 1


    def exploreRec(self, seenPartMod, idPart, maxConj):
        r = ""
        atts = list()
        mods = list()
        for m in seenPartMod:
            attN = self.vocabulary.getAttributeNames()[m[0]]
            part = self.vocabulary.getAttribute(attN)
            modN = part.getModNames()[m[1]]
            atts.append(attN)
            mods.append(modN)

        if self.mode == "real":
            calc = self.getRealConjunctionCardinality(self.vocabulary, atts,mods)
        else:
            calc = self.getEstimatedConjunctionCardinality(self.vocabulary, atts,mods)

        if calc > LIMIT:
            self.generateSummaries(atts, mods, calc)

            if maxConj == 0 or len(seenPartMod) < maxConj:

                for i in xrange(idPart,len(self.vocabulary.getAttributeNames())):
                    attN = self.vocabulary.getAttributeNames()[i]
                    for j in xrange(len(self.vocabulary.getAttribute(attN).getModNames())):
                            a = copy.deepcopy(seenPartMod)
                            a.append([i,j])
                            self.exploreRec(a,i+1,maxConj)


    def exploreSummarizersSearchSpace(self, maxConj=0):
        for i,attN in enumerate(self.vocabulary.getAttributeNames()):
            for j,modN in enumerate(self.vocabulary.getAttribute(attN).getModNames()):
                self.exploreRec([[i,j]], i+1, maxConj)
        # bilan
        print("NB SUMMARIES %d"%self.nbR)


    def exploreSummarizersSearchSpaceFast(self, maxConj=0, frels=None):
        "explore en largeur d'abord"
        # construire la liste des listes de modalités, chacune associée à son score
        # ex: [ [(a1m1,0.8), (a1m2,0.7)...], [(a2m1,0.6), (a2m2,0.9)...]...]
        # BIZARRE : c'est plus lent de précalculer les cardinalités relatives que de les calculer ensuite... sûrement la BDD qui rame
        #all_modalities_mus = map(lambda att:
        #                            map(lambda mod:
        #                                (mod,self.getEstimatedCardinalityModality(self.vocabulary, mod)[0]),
        #                                att.getModalities()),
        #                            self.vocabulary.getAttributes())
        # construire la liste des listes de modalités, chacune associée à son score (None initialement, liste pour être mutable)
        # ex: [ [[a1m1,None], [a1m2,None]...], [[a2m1,None], [a2m2,None]...]...]
        # exemple : [ [(a1m1,0.8), (a1m2,0.7), ...], [(a2m1,0.6), (a2m2,0.9), ...], ...]
        # dans la liste englobante, il y a autant d'items que d'attributs
        # chaque item est la liste de toutes les modalités de cet attribut
        # chaque modalité est un couple (modalité, sigmas) avec sigmas = triplet (sigma, sigma- et sigma+) issu de getEstimatedCardinalityModality
        all_modalities_mus = list(map(lambda att:
                                    list(map(lambda mod:
                                        [mod, None],
                                        att.getModalities())),
                                    self.vocabulary.getAttributes()))
        nbFrels = 0
        consolidatedModalities = set()
        # étudier toutes les combinaisons de longueurs croissantes de ces modalités
        for lenConj in xrange(1, maxConj+1):
            # reste vrai s'il n'y a plus aucune conjonction satisfaisante
            stop = True
            # parcourir toutes les combinaisons de modalités de longueur lenConj
            for combination in itertools.combinations(all_modalities_mus, lenConj):
                # => (item1,item2), (item1,item3), (item2, item3)... avec item = liste des modalités d'un attribut
                # parcourir tous les produits cartésiens de ces ensembles de modalités
                for conjunction in itertools.product(*combination):
                	#print("conjunction = %s"%list(map(lambda mod_sigmas: "%s/%s"%(mod_sigmas[0].getFullName(), str(mod_sigmas[1])), conjunction)))
                    # calculer les scores des modalités indéterminées
                    summarizer=list(map(lambda mod_sigmas: "%s/%s"%(mod_sigmas[0].getFullName(), str(mod_sigmas[1])), conjunction))
                    for mod_sigmas in filter(lambda mod_sigmas: mod_sigmas[1] is None, conjunction):
                        # mod_sigmas est un couple mutable (modalité, (sigma, sigma- et sigma+))
                        sigma, sigma_inf, sigma_sup = self.getEstimatedCardinalityModality(self.vocabulary, mod_sigmas[0])
                        # consolidation Frels ?
                       	#
                        if frels is not None and abs(sigma_sup - sigma_inf) >= FRELS_LIMIT:
                            print("CONSOLIDATION WITH FRELS FOR SUMMARIZER %s, sigma=%f with bounds [%f,%f]"%(summarizer,sigma,sigma_inf,sigma_sup))
                            sigma_frels = frels.checkCardinality(self.vocabulary, mod_sigmas[0])
                            print("CONSOLIDATION RESULT sigma=%f with bounds [%f,%f] -> sigmasCons = %f"%(sigma,sigma_inf,sigma_sup,sigma_frels))
                            nbFrels += 1
            	            # correction
            	            sigma = sigma_inf = sigma_sup = sigma_frels
                            consolidatedModalities.add(mod_sigmas[0])

                        # affecter les sigmas du couple (modalité, sigmas)
                        mod_sigmas[1] = sigma, sigma_inf, sigma_sup

                    # calculer la cardinalité relative de la conjonction : produit des cardinalités des membres, idem pour inf et sup
                    pi_sigma     = reduce(operator.mul, map(lambda mod_sigmas: mod_sigmas[1][0], conjunction))
                    pi_sigma_inf = reduce(operator.mul, map(lambda mod_sigmas: mod_sigmas[1][1], conjunction))
                    pi_sigma_sup = reduce(operator.mul, map(lambda mod_sigmas: mod_sigmas[1][2], conjunction))
                    if pi_sigma > LIMIT:
                    	#if frels is None or (consolidatedModalities & set(map(lambda mod_sigmas: mod_sigmas[0], conjunction)) != set()):
                    	if frels is None or (consolidatedModalities & set(map(lambda mod_sigmas: mod_sigmas[0], conjunction)) != set()):
	                        summarizer = " AND ".join(list(map(lambda mod_sigmas: "%s"%(mod_sigmas[0].getFullName()), conjunction)))
	                        if summarizer not in self.exploredProperties:
	                            self.exploredProperties[summarizer] = 0.0
	                        self.exploredProperties[summarizer] += pi_sigma
	                        self.generateSummariesModalities(map(lambda mod_sigmas: mod_sigmas[0], conjunction), pi_sigma, pi_sigma_inf, pi_sigma_sup)
	                        # on peut continuer à ce niveau
	                	stop = False
            # on arrête là si on n'a aucune conjonction de longueur lenConj
            if stop: break
        # bilan
        print("NB SUMMARIES %d"%self.nbR)
        if frels:
            print("NB FRELS CONSOLIDATIONS %d"%nbFrels)


    def getLatticeSize(self, maxConj):
        """
        retourne le nombre de noeuds dans le treillis
        NB: pas de formule à partir du nombre de modalités, d'attributs et de la profondeur
        car le nombre de modalités est variable selon les attributs du vocabulaire
        """
        size = 0
        all_modalities = map(lambda att: list(att.getModalities()), self.vocabulary.getAttributes())
        # compter toutes les combinaisons de longueurs croissantes de ces modalités
        for lenConj in xrange(1, maxConj+1):
            # parcourir toutes les combinaisons de modalités de longueur lenConj
            for combination in itertools.combinations(all_modalities, lenConj):
                # parcourir tous les produits cartésiens de ces ensembles de modalités
                for conjunction in itertools.product(*combination):
                    size += 1
        return size


    ## TENTATIVE POUR MIEUX ESTIMER LES CARDINALITÉS DES CONJONCTIONS
    #def buildConjunctionsDistinctCardinalities(self, maxConj):
    #    "construit le dictionnaire [id_node] = proba de cette conjonction"
    #    "IDEE faire une requête que sur les conjonctions les plus longues et évaluer tous les sous-ensembles"
    #    self.conjunctionsDistinctCardinalities = {}
    #    all_modalities = map(lambda att: list(att.getModalities()), self.vocabulary.getAttributes())
    #    # parcourir toutes les combinaisons de modalités de longueur lenConj
    #    for combination in itertools.combinations(all_modalities, maxConj):
    #        # parcourir tous les produits cartésiens de ces ensembles de modalités
    #        for conjunction in itertools.product(*combination):
    #            # idée : créer un identifiant de noeud dans le treillis, soit le numéro lors du parcours, soit la concaténation des noms complets des modalités
    #            print(list(map(lambda mod: mod.getFullName(), conjunction)))
    #            # demander 0.01% des tuples au système
    #            query = self.getSampleTuplesSelectedByConjunction(conjunction, 0.01)
    #            for row in query:
    #                pass
    ## PAS FINI


    def summarizeTuple(self, tup, maxConjP1):
        """
        This function initiates the dictionnary self.exploredPropertiesTmp
        with all the possible conjunctive combinations of modalities (of up to maxConj elements)
        taken from the vocabulary

        @param tup (dict) dictionary given by psycopg2.RealDictCursor containing the values associated to their attribute
        @param maxConjP1 (int) maximal number of items in conjunctions
        """
        # construire la liste des listes de modalités, chacune associée à son score de ré-écriture
        # ex: [ [(a1m1,0.8), (a1m2,0.7)...], [(a2m1,0.1), (a2m2,0.9)...]...]
        # dans la liste englobante, il y a autant d'items que d'attributs
        # note: les paires générées ont toutes un µ non nul, ce qui évite des tests
        all_modalities_mus_not_zero = list()
        for att in self.vocabulary.getAttributes():
            attN = att.getName().lower()
            try:
                value = tup[attN]
                modalities_mus_not_zero = list()
                for mod in att.getModalities():
                    mu = mod.getMu(value)
                    if mu > 0.0:
                        modalities_mus_not_zero.append( (mod, mu) )
            except KeyError:
                pass
            if len(modalities_mus_not_zero) > 0:
                all_modalities_mus_not_zero.append(modalities_mus_not_zero)
        # parcours du treillis pour calculer la cardinalité de la conjonction sur la ré-écriture
        for lenConj in xrange(1, maxConjP1):
            # parcourir toutes les combinaisons de modalités de longueur lenConj
            for combination in itertools.combinations(all_modalities_mus_not_zero, lenConj):
                # => (item1,item2), (item1,item3), (item2, item3)... avec item = liste des modalités d'un attribut
                # parcourir tous les produits cartésiens de ces ensembles de modalités
                for conjunction in itertools.product(*combination):
                    # conjunction est une liste de couples (modalité, µ(modalité))
                    #card = min(map(lambda pair: pair[1], conjunction))
                    card = reduce(operator.mul,map(lambda pair: pair[1], conjunction))
                    
                    key = tuple(map(lambda pair: pair[0], conjunction))
                    self.exploredPropertiesTmp[key] += card


    def scanDataToSummarize(self, maxConj=0, modalities=[]):
        """
        This function reads all the data in the table and computes the relative cardinalities
        of all conjunctions of the modalities if give, or all the modalities of the vocabulary

        @param modalities (list of Modality) modalities to scan
        @param maxConjP1 (int) maximal number of items in conjunctions
        """
        maxConjP1 = maxConj + 1
        # scan of all the data
        t_beg = time.time()
        cursor = self.getTuplesSelectedByConjunction(modalities, cursor_factory=psycopg2.extras.RealDictCursor)
        t_end = time.time()
        print("Time to getTuplesSelectedByConjunction = %ss"%round(t_end-t_beg, 3))
        self.nbTuplesScanned = cursor.rowcount
        print("%d tuples to scan and summarize, be patient..."%self.nbTuplesScanned)
        t_beg2 = time.time()
        nextnum = 1000
        # loop through all tuples
        self.exploredPropertiesTmp = defaultdict(int)
        num = 0
        for tup in cursor:
            self.summarizeTuple(tup, maxConjP1)
            # a message every minute
            num += 1
            if num >= nextnum:
                elapsed = time.time() - t_beg2
                minutes = elapsed / 60
                speed = int(round(num / minutes))
                if speed > 0:
                    nextnum += max(speed, 1000)
                    minutes = int(minutes)
                    togo = self.nbTuplesScanned-num
                    est = (togo + 1) / speed
                    print("%d scanned, %d:%02d elapsed, %d tuples left, %d/min, %d:%02d to go..."%(
                        num, int(minutes/60),minutes%60, togo, speed, int(est/60),est%60))
        print("... scan and summarization of %d tuples done."%(num))
        # normalisation of the sigma counts
        self.exploredProperties = dict()
        for conjunction in self.exploredPropertiesTmp.keys():
            readable = " AND ".join(map(lambda modality: modality.getFullName(), conjunction))
            self.exploredProperties[readable] = self.exploredPropertiesTmp[conjunction] / self.nbTuplesScanned


    def generateSummariesForJson(self):
        """
        Translate all the summaries into a dict that can then be stored in a Json file
        """
        sumJ = dict()
        for s in self.summaries:
            summarizer = s.getSummarizer()
            if summarizer not in sumJ:
                sumJ[summarizer] = []
            #print("%s -> %s"%(summarizer, s.getQuantifier().getLabel()))
            sumJ[summarizer].append(s.getQuantifier().getLabel())
        return sumJ


    def generateSummaries(self):
        """
        Generation of the summaries
        @return a generator on the Summary objects  list
        """
        for summarizer in self.exploredProperties.keys():
            # limite minimale
            if self.exploredProperties[summarizer] > LIMIT:
                # quantificateurs pouvant décrire la cardinalité relative
                matching_quantifiers = self.quantifiers.getMatchingQuantifiers(self.exploredProperties[summarizer])
                # générer un résumé pour chaque quantificateur
                for quantifier, score in matching_quantifiers:
                    s = Summary(self.tablename, quantifier, None, summarizer, quantifier, self.exploredProperties[summarizer])
                    self.summaries.append(s)
                    self.nbR += 1
                    yield s

        #print("NB SUMMARIES %d (over %d properties)"%(self.nbR,len(self.exploredProperties.keys())))


    def compare(self, s1, s2):#s1 and s2 are two summaries
        r = 0
        print("Summaries not present in the second summary")
        for s in self.summaries:
            if s in s2.summaries:
                r += 1
            else:
                print(s)
        print("INTERSECTION RATIO %f"%(float(r)/len(self.summaries)))


    def distance(self, s1, s2):
        ret = abs((s1.quantifier.getIndex() - s1.truth) - (s2.quantifier.getIndex() - s2.truth))/(self.quantifiers.nbQuantifiers()-1.0)
        return ret


    def compareSummaries(self, sums):
        mi = 1
        ma = 0
        su = 0

        for s in self.summaries:

            i = 0
            while i < len(sums.summaries) and s.getCode() != sums.summaries[i].getCode():
                i += 1

            if i < len(sums.summaries):
                d = self.distance(s,sums.summaries[i])
            #   print(s.linguisticStatement()+" : "+str(d))
                if d < mi:
                    mi = d
                if d > ma:
                    ma = d
                su += d
            else:
                d = (s.quantifier.getIndex() - s.truth) / (self.quantifiers.nbQuantifiers() - 1.0)
                ma = d
                su += d
                print("NOT FOUND : "+s.linguisticStatement()+" : "+str(d))
                #not present
        return mi, su/len(self.summaries), ma




# se connecter à la base et lancer le travail
if __name__ == "__main__":

    # default parameters
    maxC = 2
    #vocFile = '../Data/miniVoc.txt'
    #vocFile = '../Data/FlightsVoc.txt'
    vocFile = '../Data/flights_numerical.txt'
    #vocFile = '../Data/flightsVoc_numerical_frels.txt'
    host = 'localhost'
    database = 'flights'
    table = 'flights_2008_300k_1'

    # help
    def usage():
        print('usage:  [python2|python3] %s [options] actions*'%sys.argv[0])
        print('options:')
        print('  -m N, --maxc=N     : maximal number of items in conjunctions, default "%d"'%maxC)
        print('  -v F, --voc=F      : filename of the vocabulary, default "%s"'%vocFile)
        print('  -h S, --host=S     : hostname of the postgresql server, default "%s"'%host)
        print('  -d S, --database=S : name of the database, default "%s"'%database)
        print('  -t S, --table=S    : name of the table, default "%s"'%table)
        print('actions:')
        print('  scan     : Summarization with real data scan')
        print('  query    : Summarization with data query')
        print('  estimate : Summarization with estimations based on database metadata')
        print('  frels    : Summarization with estimations, consolidated with queries')
        print('note: you may have a ~/.pgpass file containing your login and password')

    # parse parameters if any
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:v:h:d:t:", ("maxc=", "voc=", "host=", "database=", "table="))
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-m", "--maxc"):
            try:
                maxC = int(arg)
            except ValueError:
                print('Error in option %s : "%s" is not an integer type'%(opt, arg))
                sys.exit(2)
        elif opt in ("-v", "--voc"):
            if os.path.isfile(arg):
                vocFile = arg
            else:
                print('Error in option %s : "%s" is not an existing file'%(opt, arg))
                sys.exit(2)
        elif opt in ("-h", "--host"):
            host = arg
        elif opt in ("-d", "--database"):
            database = arg
        elif opt in ("-t", "--table"):
            table = arg
        else:
            print(opt)
            usage()
            sys.exit(2)
    for arg in args:
        if arg not in ('scan', 'query', 'estimate', 'frels'):
            print('"%s" is not an allowed action'%arg)
            usage()
            sys.exit(2)

    # lancement par F5 dans Idle
    if args == []:
        args = ['estimate', 'frels']


    # read vocabulary from file
    vocabulary = Vocabulary(vocFile)

    # quantifiers
    quantifiers = QuantifierDistribution()

    # test du résumeur par interrogation des données
    if 'scan' in args:
        with Summarizer(host, database, table, vocabulary, quantifiers, 'scan') as s_scan:

            ep_real_json_filename = 'ExploredProperties_max%d_%s_scan.json'%(maxC, table)
            if os.path.isfile(ep_real_json_filename):
                # re-Read exploredProperties from file
                with open(ep_real_json_filename, 'rt') as jsonfile:
                    s_scan.exploredProperties = json.loads(jsonfile.read())

                print("Summarization with already scanned data in %s"%ep_real_json_filename)
                t_beg = time.time()
            else:
                # do the full and slow scan
                print("Summarization with data scan:")
                t_beg = time.time()
                s_scan.scanDataToSummarize(maxC, [])
                t_end = time.time()
                print("scan completed = %ss"%round(t_end-t_beg, 3))

                # Save exploredProperties into file
                with open(ep_real_json_filename, 'wt') as jsonfile:
                    jsonfile.write(json.dumps(s_scan.exploredProperties, sort_keys=True, indent=4))
                    print("Wrote %s"%ep_real_json_filename)

            for s in s_scan.generateSummaries():
                print(s)

            t_end = time.time()
            gs_real_json_filename = 'GeneratedSummaries_max%d_%s_scan.json'%(maxC, table)
            if not os.path.isfile(gs_real_json_filename):
                 # Save linguistic summaries into file
                with open(gs_real_json_filename, 'wt') as jsonfile:
                    jsonfile.write(json.dumps(s_scan.generateSummariesForJson(), sort_keys=True, indent=4))
                    print("Wrote %s"%gs_real_json_filename)

            print("Elapsed time = %ss"%round(t_end-t_beg, 3))

            print("*******************************\n")
            print("*******************************\n")


    # test du résumeur par interrogation des données
    if 'query' in args:
        with Summarizer(host, database, table, vocabulary, quantifiers, 'real') as s_real:
            print("Summarization with data querying:")
            t_beg = time.time()
            s_real.exploreSummarizersSearchSpace(maxC)
            t_end = time.time()
            print("Elapsed time = %ss"%round(t_end-t_beg, 3))

            print("*******************************\n")
            print("*******************************\n")
            print("*******************************\n")
            print("*******************************\n")

            try:
                mi,mo,ma = s_real.compareSummaries(s_scan)
                print("DISTANCE COMPUTATION BETWEEN REALQUERY AND SCANDATA and min="+str(mi)+" avg="+str(mo)+" max="+str(ma))
            except Exception as e:
                print(e+" => no comparison between realquery and scandata")


    # test du résumeur rapide sur les estimations
    if 'estimate' in args:
        with Summarizer(host, database, table, vocabulary, quantifiers, 'estimate') as s_estimate:

            print("Summarization with Estimations V2 without FRELS:")
            t_beg = time.time()
            s_estimate.exploreSummarizersSearchSpaceFast(maxC)
            t_end = time.time()

            for s in s_estimate.generateSummaries():
                print(s)

            # Explored Properties
            ep_est_json_filename = 'ExploredProperties_max%d_%s_estimate.json'%(maxC, table)
            with open(ep_est_json_filename, 'wt') as jsonfile:
                jsonfile.write(json.dumps(s_estimate.exploredProperties, sort_keys=True, indent=4))
                print("Wrote %s"%ep_est_json_filename)

            # Generated Summaries
            gs_est_json_filename = 'GeneratedSummaries_max%d_%s_estimate.json'%(maxC, table)
            with open(gs_est_json_filename, 'wt') as jsonfile:
                jsonfile.write(json.dumps(s_estimate.generateSummariesForJson(), sort_keys=True, indent=4))
                print("Wrote %s"%gs_est_json_filename)

            print("Elapsed time = %ss"%round(t_end-t_beg, 3))


     # test du résumeur rapide sur les estimations avec FRELS activé
    if 'frels' in args:
        with Summarizer(host, database, table, vocabulary, quantifiers, 'estimate') as s_frels:
            frels = Frels(s_frels)
            print("Summarization with Estimations V2 with FRELS :")
            t_beg = time.time()
            s_frels.exploreSummarizersSearchSpaceFast(maxC, frels)
            t_end = time.time()

            for s in s_estimate.generateSummaries():
            	print(s)

            # Explored Properties
            ep_frels_json_filename = 'ExploredProperties_max%d_%s_frels.json'%(maxC, table)
            with open(ep_frels_json_filename, 'wt') as jsonfile:
                jsonfile.write(json.dumps(s_frels.exploredProperties, sort_keys=True, indent=4))
                print("Wrote %s"%ep_frels_json_filename)

            # Generated Summaries
            gs_frels_json_filename = 'GeneratedSummaries_max%d_%s_frels.json'%(maxC, table)
            with open(gs_frels_json_filename, 'wt') as jsonfile:
                jsonfile.write(json.dumps(s_frels.generateSummariesForJson(), sort_keys=True, indent=4))
                print("Wrote %s"%gs_frels_json_filename)

            print("Elapsed time = %ss"%round(t_end-t_beg, 3))

