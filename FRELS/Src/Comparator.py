#!/usr/bin/python
# -*- coding: UTF-8 -*-


import sys
import json
import os
import getopt



def compareProperties(refPropFile, testPropFile, debug=True):
    """

    """
    sumDiff = 0
    maxDiff = 0
    notfound = 0

    # read reference file into refProp dictionary
    with open(refPropFile, 'rt') as jsonfile:
        refProp = json.loads(jsonfile.read())

    # read test file into testProp dictionary
    with open(testPropFile, 'rt') as jsonfile:
        testProp = json.loads(jsonfile.read())

    # loop through all properties in reference file
    for prop, cardR in refProp.items():
        if cardR is None:
            raise Exception("cardinality is None for %s in %s"%(prop, refPropFile))
        if prop in testProp:
            # get cardinality in test file
            cardT = testProp[prop]
            if cardT is None:
                raise Exception("cardinality is None for %s in %s"%(prop, testPropFile))

            # error
            diff = abs(cardR - cardT)
            sumDiff += diff
            if maxDiff < diff: maxDiff = diff

            if debug: print("Properties %s: |ref(%f) - test(%f)| = %f"%(
                prop, cardR, cardT, diff))

        else:
            if debug: print("%s not found in %s"%(prop,testPropFile))
            notfound += 1

    if debug:
        print("*********************************\n")
        print("%s versus %s"%(refPropFile, testPropFile))
    print("%d properties compared, %f difference in average, %f maximal difference, with %d not found."%(
        len(refProp), sumDiff/len(refProp), maxDiff, notfound))


def compareSummaries(refSumFile, testSumFile, quantDist=None, debug=True):
    """
    refSumFile is the name of the file containing the reference summaries (association of a summarizer and quantifier(s))
    testSumFile is the name of the file containing the summaries to check (association of a summarizer and quantifier(s))
    quantDist is an instance of the QuantifiersDistribution class that could be used to compute a distance between the expected and found quantifier
    """
    sumDiff = dict()     # {quantifier associated to a pair (nbExpected, nbFound, errors)}

    # read reference file into refQuant dictionary
    with open(refSumFile, 'rt') as jsonfile:
        refQuant = json.loads(jsonfile.read())

    # read test file into testQuant dictionary
    with open(testSumFile, 'rt') as jsonfile:
        testQuant = json.loads(jsonfile.read())

    # loop through all summaries in reference file
    for prop, quantsR in refQuant.items():
        # quantsR is a list of quantifiers, i.e. ['Few', 'Around half']
        for quantR in quantsR:
            # new quantifier ?
            if quantR not in sumDiff:
                sumDiff[quantR] = [0, 0, dict()]
            # one more summary in the ref file, to expect in test file
            sumDiff[quantR][0] += 1

            if prop in testQuant:
                quantsT = testQuant[prop]           
                if quantR not in quantsT:
                    if debug: print("WRONG QUANTIFIER FOR SUMMARIZER %s, EXPECTING %s, FOUND %s"%(prop, quantR, quantsT))
                    errors = sumDiff[quantR][2]
                    for quantT in quantsT:
                        if not quantT in errors:
                            errors[quantT] = 1
                        else:
                            errors[quantT] += 1
                else:
                    sumDiff[quantR][1] += 1
            else:
                if debug: print("MISSING %s, EXPECTING %s"%(prop, quantR))

    if debug:
        print("*********************************\n")
        print("%s versus %s"%(refSumFile, testSumFile))
    for quant, (expected, found, errors) in sumDiff.items():
        print("\t- %s\t: expected %d, found %d, missing %d, errors=%s"%(quant, expected, found, expected-found, errors))
    # TODO afficher des totaux, mais quelle utilité ?



if __name__ == "__main__":

    # default parameters
    debug = True

    # help
    def usage():
        print('usage:  [python2|python3] %s [-q|--quiet] [properties|summaries] <fileRef.json> <comparedFile.json>'%sys.argv[0])

    # parse parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:], "q", ("quiet"))
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-q', '--quiet'):
            debug = False

    # number of mandatory parameters
    if len(args) != 3:
        usage()
        sys.exit(1)

    # first mandatory parameter : properties|summaries
    kind = args[0].lower()
    if not kind in ('properties', 'prop', 'summaries', 'sum'):
        usage()
        sys.exit(1)

    # second mandatory parameter : reference filename
    if not os.path.isfile(args[1]):
        print("File %s not found"%args[1])
        sys.exit(3)

    # third mandatory parameter : test filename
    if not os.path.isfile(args[2]):
        print("File %s not found"%args[2])
        sys.exit(4)

    # work
    if kind in ('properties', 'prop'):
        compareProperties(args[1], args[2], debug=debug)
    else:
        compareSummaries(args[1], args[2], debug=debug)
