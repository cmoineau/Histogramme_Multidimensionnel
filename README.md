# Multidmensional histogram
Implémentation de 3 histogrammes multidimensionnel avec `python 3.6` : MHIST (ref.1), GENHIST (ref.2) et ST-HOLES (ref.3).
Création d'une API `dockerisé`  avec la librairie `FLASK`.
L'objectif des histogrammes est de donner des estimations de la cardinalité de requête sur plusieurs attributs.

## Présentation de l’API :

L’objectif de l’API et d’avoir une interface pour manipuler les objets histogrammes.
Pour cela, j’ai créé un wrapper pour interagir avec les histogrammes sérialisé. 

L’API doit répondre aux besoins suivant : 

* Créer un histogramme :
    * MHIST
    * GENHIST
    * STHoles
* Faire une estimation à partir d'un histogramme
* Obtenir la liste des attributs d'un histogramme
* Pour STHoles mettre à jour l'histogramme
    
Le wrapper permet en plus de l’API d’afficher des représentations graphiques des histogrammes, ce qui n’est pas possible avec l’API.

Toutes mauvaises requêtes  renverront vers la page de documentation de l’API grâce à une redirection sur les erreurs 404. 

POST :
---

* **creer/stholes/ :**
    
**Description :** Créer un histogramme stholes.

**Entrée :** un json contenant les champ : nom_attributs, nom_histogrammes.

**Sortie :** un json avec le champ : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête.

**Exemple d’entrée :** 
> curl -X POST -H 'Content-Type: application/json' -i http://localhost:5000/creer/stholes/ --data '{"nom_attributs":["x"], "nom_histogramme":"toto"}'

* **creer/mhist/ :**

**Description :** Créer un histogramme mhist.

**Entrées :**  un json contenant les champ : nom_attributs, nom_histogrammes, donnee.

**Sortie :** un json avec le champ : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête.

**Exemple d’entrée :** 
>curl -X POST -H 'Content-Type: application/json' -i http://localhost:5000/creer/mhist/ --data '{"nom_attributs":["x"], "nom_histogramme":"toto", "donnee": [[1, 2, 3, 4, 5, 6 ,1]]}'

* **creer/genhist/ :**

**Description :** Créer un histogramme genhist.

**Entrée :** Un json contenant les champs : nom_attributs, nom_histogrammes, donnee.

**Sortie :** un json avec le champs : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête.

**Exemple d’entrée :** 
>curl -X POST -H 'Content-Type: application/json' -i http://localhost:5000/creer/genhist/ --data '{"nom_attributs":["x"], "nom_histogramme":"toto", "donnee": [[1, 2, 3, 4, 5, 6 ,1]]}'

* **<nom_histogramme>/estimer/ :**

**Description :** Permet de réaliser une estimation d’une zone avec l’histogramme <nom_histogramme>. Pour obtenir le nom de l’histogramme de référer à la méthode lister.

**Entrée :** Un json : contenant les champs : nom_attributs,  zone.

**Sortie :** un json avec le champs : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête, resultat : résultat de l’estimation.

**Exemple d’entrée :**
> curl -X POST -H 'Content-Type: application/json' -i 'http://localhost:5000/test.genhist/estimer' --data '{"nom_attributs": ["x"], "zone":[[-1, 1]]}'

GET :
---
* **lister_histogrammes/ :**

**Description :** Renvoit la liste des histogrammes sérialisés.

**Entrée :** Un json : contenant les champs : nom_attributs,  zone.

**Sortie :** un json avec le champs : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête, resultat : résultat de l’estimation.

**Exemple d’entrée :**
> curl -X POST -H 'Content-Type: application/json' -i 'http://localhost:5000/test.genhist/estimer' --data '{"nom_attributs": ["x"], "zone":[[-1, 1]]}'

* **<nom_histogramme>/attributs :**

**Description :** Renvoit la liste des attributs de l’histogramme <nom_histogramme>.

**Entrée :** None.

**Sortie :** un json avec le champs : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête, resultat : liste des attribut.

**Exemple d’entrée :**
> curl -X POST -H 'Content-Type: application/json' -i 'http://localhost:5000/test.genhist/estimer' --data '{"nom_attributs": ["x"], "zone":[[-1, 1]]}'

DELETE :
---
* **<nom_histogramme>/ :**

**Description :** Permet de supprimer côté serveur un histogramme sérialisé

**Entrée :** None

**Sortie :** un json avec le champs : status : indique si la requête c’est bien déroulée, message : Description du déroulement de la requête

**Exemple d’entrée :**
> curl -X POST -H 'Content-Type: application/json' -i 'http://localhost:5000/test.genhist/estimer' --data '{"nom_attributs": ["x"], "zone":[[-1, 1]]}'


## Dockerisation de l’application :

Pour créer et utiliser l’application dockerisé, rendez vous à la racine du projet.

Ici lancez la commande :

> docker build -t api_histogramme .

Cette commande devrait construire le container. Si l’opération c’est bien déroulée, la dernière ligne devrait-être : 

> Successfully built <identifiant> 

La dernière étape consiste à démarrer le container avec la commande :

> docker run -p 5000:5000  api_histogramme

L’API devrait être lancé et écouter sur le port 5000. Si vous voulez changer le port d’écoute, vous devez modifier le fichier dockerfile situé à la racine ainsi que le fichier `/API/main.py`. 

## References :
  - **[1]** POOSALA, Viswanath et IOANNIDIS, Yannis E. Selectivity estimation without the attribute value independence assumption. In : VLDB. 1997. p. 486-495.
  - **[2]** Gunopulos, Dimitrios & Kollios, George & Tsotras, Vassilis & Domeniconi, Carlotta. (2001). Approximating Multi-Dimensional Aggregate Range Queries Over Real Attributes. SIGMOD Record (ACM Special Interest Group on Management of Data). 29. 10.1145/342009.335448. 
  - **[3]** BRUNO, Nicolas, CHAUDHURI, Surajit, et GRAVANO, Luis. STHoles: a multidimensional workload-aware histogram. In : Proceedings of the 2001 ACM SIGMOD international conference on Management of data. 2001. p. 211-222.
