"""
Tuto : https://wiki.postgresql.org/wiki/Psycopg2_Tutorial
"""
import psycopg2


# Variable à mettre dans un fichier plus tard ...
user = "'docker'"
host = "'172.17.0.2'"
pwd = "'docker'"
dbname = "'flights'"

# Connexion à la base de données
try:
    conn = psycopg2.connect("dbname=" + dbname + " user=" + user + " host=" + host + " password=" + pwd)
except:
    print("I am unable to connect to the database")
cursor = conn.cursor()


def get_tables_name():
    cursor.execute("SELECT * FROM information_schema.tables WHERE table_schema = 'public'")
    tables_name = [row[2] for row in cursor.fetchall()]
    return tables_name

# Requête pour obtenir le nom des différentes tables
tables_name = get_tables_name()
for name in tables_name:
    print('TABLE : ' + name)
    cursor.execute("SELECT * FROM " + tables_name[0])
    rows = cursor.fetchall()
    for row in rows:
        string = ""
        for i in row:
            string += str(i) + ' | '
        # print(string)


