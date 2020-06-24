from API import wrapper
from flask import Flask, jsonify, request

app = Flask(__name__)

wrapper = wrapper.Histogramme_wrapper()


@app.route('/STholes/', methods=['POST'])
def creer_stholes():
    # récupère sous la forme d'un json les paramètres.
    payload = request.get_json()
    try:
        attributes_name = payload['attributes_name']
        path = payload['nom_histogramme']
    except Exception as e:
        return jsonify(status='False', message="Vous devez spécifier le nom des attributs et le nom de l'histogramme")
    result = wrapper.create_STHoles(attributes_name, path)
    if result:
        return jsonify(status='True', message='Histogramme crée avc succès !')
    return jsonify(status='False', message="Erreur lors de la création de l'histogramme ...")


@app.route('/mhist/', methods=['POST'])
def creer_mhist():
    # récupère sous la forme d'un json les paramètres.
    payload = request.get_json()
    try:
        attributes_name = payload['attributes_name']
        path = payload['nom_histogramme']
        data = payload['donnee']
    except Exception as e:
        return jsonify(status='False', message="Vous devez spécifier le nom des attributs et le nom de l'histogramme")
    result = wrapper.create_MHIST(data, attributes_name, path)
    if result:
        return jsonify(status='True', message='Histogramme crée avc succès !')
    return jsonify(status='False', message="Erreur lors de la création de l'histogramme ...")


@app.route('/genhist/', methods=['POST'])
def creer_genhist():
    # récupère sous la forme d'un json les paramètres.
    payload = request.get_json()
    try:
        attributes_name = payload['attributes_name']
        path = payload['nom_histogramme']
        data = payload['donnee']
    except Exception as e:
        return jsonify(status='False', message="Vous devez spécifier le nom des attributs et le nom de l'histogramme")
    result = wrapper.create_GENHIST(data, attributes_name, path)
    if result:
        return jsonify(status='True', message='Histogramme crée avc succès !')
    return jsonify(status='False', message="Erreur lors de la création de l'histogramme ...")


# J'aurais aimer le mettre en GET mais je n'ai pas trouver comment avoir un payload avec GET
@app.route('/<nom_histogramme>/estimer', methods=['POST'])
def estimer(nom_histogramme=None):
    payload = request.json
    path = "./saved_hist/" + nom_histogramme
    try:
        attributes_name = payload['nom_attributs']
        zone = payload["zone"]
    except Exception as e:
        return jsonify(status='False', message="Vous devez spécifier le nom des attributs et le nom de l'histogramme")

    try:
        wrapper.load_histogramme(path)
    except Exception as e:
        return jsonify(status='False', message="Impossible de trouver l'histogramme\n")
    result = wrapper.estimer(attributes_name, zone)
    return jsonify(status='True', resultat=result)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
