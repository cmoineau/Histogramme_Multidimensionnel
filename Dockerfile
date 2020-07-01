# On crée notre container à partir d'un container déjà existant
FROM python:alpine3.7 

# Copie des scripts dans un dossier app
COPY ./API /app/API
COPY ./MHIST /app/MHIST
COPY ./GENHIST /app/GENHIST
COPY ./STHOLES /app/STHOLES
COPY requirements.txt /app/
COPY utils.py /app/

# Mise en place du dossier de travail
WORKDIR /app/API

# Création d'un volume pour avoir une persistance des données
VOLUME  ["/app/"]

# Importation des bibliothèques Python
RUN pip install --upgrade pip
RUN pip install -r ../requirements.txt

# Mise en place du port sur lequel l'API répondra 
EXPOSE 5000 

# Cette ligne annonce qu'il faut interprêter les commandes avec PYTHON (cf. documentation DOCKER)
ENTRYPOINT [ "python" ] 

# Lancement de l'API
CMD [ "main.py" ] 

