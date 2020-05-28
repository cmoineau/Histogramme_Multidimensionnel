import json
path = './DATA/test_random.json'
# path = 'TEST_1.json'
# path = 'TEST_2.json'

if __name__ == '__main__':
    with open(path, 'r') as f:
        resultats = json.load(f)
        mhist_err = 0
        genhist_err = 0
        stholes_err = 0
        quotient_norm = 0
        for k, v in resultats["Resultat"].items():
            if k != "time" and k != "size":
                reel = v["reel"]["resultat"]
                mhist_err = abs(v["MHIST"]["resultat"] - reel)
                genhist_err = abs(v["GENHIST"]["resultat"] - reel)
                stholes_err = abs(v["STHOLES"]["resultat"] - reel)
                quotient_norm = abs(v["AVI"]["resultat"] - reel)
        print('Normalized Absolute Error :', '\n',
              'MHIST :', mhist_err / quotient_norm, '\n',
              'GENHIST :', genhist_err / quotient_norm, '\n',
              'STHOLES :', stholes_err / quotient_norm
              )