import random

from flask import Flask, render_template
import mysql.connector as mariadb

from config import db_host, db_port, db_user, db_password, db_name

app = Flask(__name__)


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/generate')
def generate():
    mariadb_connection = mariadb.connect(host=db_host, port=db_port, user=db_user, password=db_password,
                                         database=db_name)

    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute('SELECT id FROM post WHERE category IS NULL')
    rows = cursor.fetchall()
    mariadb_connection.close()
    if cursor.rowcount == 0:
        return render_template('alldone.html')
    else:
        id = random.choice(rows)[0]
        return getbeitrag(id)

app.jinja_env.globals.update(generate=generate)

@app.route('/beitrag/<beitrag_id>')
def getbeitrag(beitrag_id):
    mariadb_connection = mariadb.connect(host=db_host, port=db_port, user=db_user, password=db_password,
                                         database=db_name)

    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute('SELECT text,num_likes,num_shares FROM post WHERE id = "' + str(beitrag_id) + '"')
    if cursor.rowcount == 0 or cursor.rowcount > 1:
        raise ValueError
    row = cursor.fetchall()[0]
    beitrag = {'text': row[0], 'anzahl_likes': row[1], 'anzahl_shares': row[2]}
    mariadb_connection.close()
    return render_template('beitrag.html', beitrag=beitrag)


if __name__ == '__main__':
    app.run()
