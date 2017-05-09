import os
from random import randint

import mysql.connector as mariadb
import requests
from flask import Flask, render_template
from flask import Flask, render_template, flash
from flask import redirect
from flask import request
from flask import url_for
from flask_httpauth import HTTPBasicAuth

from config import db_host, db_port, db_user, db_password, db_name, users, api_access_token_value

app = Flask(__name__)
auth = HTTPBasicAuth()
app.secret_key = 'I4GAOnCxM3G9gCV0op9KW926L36y5evk'

api_url = 'https://graph.facebook.com/v2.9/'
api_access_token_name = 'access_token'
api_post_field_name = 'fields'
api_post_field_value = 'source,picture'

payload = {api_access_token_name: api_access_token_value, api_post_field_name: api_post_field_value}

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/generate')
def generate():
    try:
        mariadb_connection = get_db_connection()
        cursor = mariadb_connection.cursor(buffered=True)
        random = randint(1, 10)

        if random == 1:
            cursor.execute('SELECT post_id FROM category WHERE post_id NOT IN (SELECT post_id FROM category ' +
                           'WHERE user = "' + auth.username() + '")' +
                           'GROUP BY post_id ORDER BY count(post_id) ASC, rand() LIMIT 1')
        if random != 1 or cursor.rowcount == 0:
            cursor.execute('SELECT id FROM post WHERE id NOT IN (SELECT post_id from category) ORDER BY rand() LIMIT 1')

        if cursor.rowcount == 0:
            return render_template('alldone.html')
        else:
            rows = cursor.fetchone()
            post_id = rows[0]
            return redirect(url_for('getpost', post_id=post_id))
    finally:
        mariadb_connection.close()


@app.route('/post/<post_id>')
def getpost(post_id):
    # open database connection
    mariadb_connection = get_db_connection()

    # get post info from the database
    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute(
        'SELECT text,num_likes,num_shares,num_angry,num_haha,num_wow,num_love,num_sad,name,type, picture,source,permanent_link,date, paid FROM post WHERE id = "' + str(
            post_id) + '"')
    if cursor.rowcount == 0 or cursor.rowcount > 1:
        raise ValueError
    row = cursor.fetchall()[0]

    type = row[9].upper()
    picture = row[10]
    source = row[11]

    r = requests.get(api_url + post_id, params=payload)

    # retrieve new video or picture url as these expire after some time
    if type in ['VIDEO', 'PHOTO']:
        source = r.json().get('source')
        picture = r.json().get('picture')

    post = {'text': row[0], 'num_likes': row[1], 'num_shares': row[2], 'num_angry': row[3], 'num_haha': row[4],
            'num_wow': row[5], 'num_love': row[6], 'num_sad': row[7], 'name': row[8], 'type': type,
            'picture': picture, 'source': source, 'perm_link': row[12], 'date': row[13], 'paid': row[14],
            'id': post_id}
    cursor.execute('SELECT text from comment where post_id ="' + post_id + '"')

    # add comments
    post['comments'] = []
    comments = cursor.fetchall()
    for comment in comments:
        if comment[0].strip() != "":
            post['comments'].append(comment[0])

    post['num_comments'] = len(post['comments'])
    cursor.execute('SELECT id, name FROM category_name')
    category_names = cursor.fetchall()
    # close database connection
    mariadb_connection.close()

    # retrun post page
    return render_template('post.html', post=post, category_names=category_names)


@app.route('/update', methods=['POST'])
@auth.login_required
def update():
    # Read form from request
    cat = request.form.get("category", None)
    succ = request.form.get('success', None)
    sentiment = request.form.get('sentiment', None)
    id = request.form["post_id"]

    if cat is None:
        flash('Bitte wählen Sie eine Kategorie aus.')
    if succ is None:
        flash('Bitte wählen Sie aus, ob dieser Post erfolgreich war oder nicht.')
    if sentiment is None:
        flash('Bitte wählen Sie aus, ob die Stimmung aller Kommentare positiv, neutral oder negativ ist.')

    return redirect(url_for('getpost', post_id=id))

    # Build statements
    stmt = "REPLACE INTO category(user, post_id, category_name_id, sentiment, successful) VALUES(%s, %s, %s, %s, %s)"

    # Update Record in Database
    print('Updating record ' + str(id))
    connection = get_db_connection()
    cursor = connection.cursor(buffered=True)
    cursor.execute(stmt, (auth.username(), id, cat, sentiment, succ))
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
    app.run(host='0.0.0.0', port=port)  # NOSONAR
