import os
import random

from flask import Flask, render_template
import mysql.connector as mariadb
from flask import redirect
from flask import request
from flask import url_for

from config import db_host, db_port, db_user, db_password, db_name

app = Flask(__name__)


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/generate')
def generate():
    mariadb_connection = get_db_connection()
    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute('SELECT id FROM post WHERE category IS NULL')
    rows = cursor.fetchall()
    mariadb_connection.close()
    if cursor.rowcount == 0:
        return render_template('alldone.html')
    else:
        post_id = random.choice(rows)[0]
        return redirect(url_for('getpost', post_id=post_id))


@app.route('/post/<post_id>')
def getpost(post_id):
    mariadb_connection = get_db_connection()

    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute(
        'SELECT text,num_likes,num_shares,num_angry,num_haha,num_wow,num_love,num_sad,name,type FROM post WHERE id = "' + str(
            post_id) + '"')
    if cursor.rowcount == 0 or cursor.rowcount > 1:
        raise ValueError
    row = cursor.fetchall()[0]
    post = {'text': row[0], 'num_likes': row[1], 'num_shares': row[2], 'num_angry': row[3], 'num_haha': row[4],
            'num_wow': row[5], 'num_love': row[6], 'num_sad': row[7], 'name': row[8], 'type': row[9].upper(), 'num_comments': 0, 'id': post_id}
    mariadb_connection.close()
    return render_template('post.html', post=post)


@app.route('/update', methods=['POST'])
def update():
    # Read form from request
    cat = request.form["category"]
    succ = request.form['success']
    sentiment = request.form['sentiment']
    id = request.form["post_id"]

    # Build statements
    stmt = 'UPDATE post SET category = "' + cat + '" WHERE id = "' + id + '"'
    stmt2 = 'UPDATE post SET successful = ' + str(succ) + ' WHERE id = "' + id + '"'

    # Update Record in Database
    print('Updating record ' + str(id))
    connection = get_db_connection()
    cursor = connection.cursor(buffered=True)
    cursor.execute(stmt)
    cursor.execute(stmt2)
    connection.commit()
    connection.close()

    # Return to generate page for a new post
    return generate()


# Private getter to create a connection object
def get_db_connection():
    return mariadb.connect(host=db_host, port=db_port, user=db_user, password=db_password,
                           database=db_name)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
