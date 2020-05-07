#!/usr/bin/python
# -*- coding: utf8 -*-

# Met en forme le fichier csv des vols afin de pouvoir être lu par PostgreSQL pour construire
# la table Flights :
# - il remplace les "NA" par des chaînes vides
# - il analyse les chaînes HHMM pour en faire des réels représentant l'heure, ex: 3.5 = 3h30
# - il encadre des chaines vides par des ""
# Il est destiné à travailler dans un tube :
# curl -s http://stat-computing.org/dataexpo/2009/1989.csv.bz2 | bzcat | ./process_flights.py

import sys


def parseHHMMasFloat(hhmm):
    """
    Analyse la chaîne HHMM qui est fournie afin de la retourner sous forme d'un réel
    donnant le nombre d'heures. Par exemple parseHHMMasFloat('648'), à lire 6h48 retourne 6.8
    """
    if hhmm == '': return ''
    # ajouter des 0 non significatifs devant afin que 730 soit lu comme 07h30
    hhmm = '0000'+hhmm
    # extraire l'heure et la minute par rapport à la fin de la chaîne
    hh = float(hhmm[-4:-2])
    mm = float(hhmm[-2:])
    # en faire un réel représentant les heures, le retourner en chaîne
    return str(hh + mm/60.0)


# sauter la première ligne : celle des noms des colonnes
print sys.stdin.readline().strip()

# traiter les lignes suivantes
for line in sys.stdin:
    # nettoyer la ligne des espaces et saut de ligne
    line = line.strip()
    # couper la ligne en mots
    columns = line.split(',')
    # remplacer NA par une chaîne vide
    columns = map(lambda s: '' if s == 'NA' else s, columns)
    # remplacer les champs horaires par une valeur réelle
    for i in [4,5,6,7]:
        if columns[i] != "":
            columns[i] = parseHHMMasFloat(columns[i])
    # encadrer les champs chaînes par des double-quotes "
    for i in [8,10,16,17,22]:
        if columns[i] != "":
            columns[i] = '"'+columns[i]+'"'
    # regrouper les champs en une seule chaîne et l'afficher
    print ','.join(columns)
    


