import sqlite3

conn = sqlite3.connect("incidencias.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM incidencias")
rows = cursor.fetchall()

for fila in rows:
    print(fila)

conn.close()

