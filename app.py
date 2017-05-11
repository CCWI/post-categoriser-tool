import ast
import os
from random import randint

import mysql.connector as mariadb
import json
import requests
from datetime import datetime
from flask import Flask, render_template
from flask import Flask, render_template, flash, abort
from flask import redirect
from flask import request
from flask import url_for
from flask_httpauth import HTTPBasicAuth
from tree import build_tree, sort_tree

from config import db_host, db_port, db_user, db_password, db_name, users, api_access_token_value

app = Flask(__name__)
auth = HTTPBasicAuth()
app.secret_key = 'I4GAOnCxM3G9gCV0op9KW926L36y5evk'

api_url = 'https://graph.facebook.com/v2.9/'
api_access_token_name = 'access_token'
api_post_field_name = 'fields'
api_post_field_value = 'source,full_picture'

payload = {api_access_token_name: api_access_token_value, api_post_field_name: api_post_field_value}


@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None


@app.route('/')
def main():
    total = 0
    current = 0
    percent = 0
    mariadb_connection = get_db_connection()
    cursor = mariadb_connection.cursor(buffered=True)
    cursor.execute(
        'SELECT count(distinct p.id), count(distinct c.post_id), round(count(distinct c.post_id)/count(distinct p.id)*100,2) FROM post p LEFT JOIN category c on (p.id = c.post_id)')
    if cursor.rowcount != 0:
        row = cursor.fetchone()
        total = row[0]
        current = row[1]
        percent = row[2]

    statistic = {"total": total,
                 "current": current,
                 "percent": percent}
    return render_template('index.html', statistic=statistic)


@app.route('/help')
def help():
    return render_template('help.html')


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
        'SELECT p.text,p.num_likes,p.num_shares,p.num_angry,p.num_haha,p.num_wow,p.num_love,p.num_sad,p.name,p.type,p.picture,p.source,p.permanent_link,p.date,p.paid,pg.owner FROM post p JOIN page pg ON (p.page_id = pg.id) WHERE p.id = %s',
        (post_id,))
    if cursor.rowcount == 0 or cursor.rowcount > 1:
        abort(404)
    row = cursor.fetchall()[0]

    type = row[9].upper()
    picture = row[10]
    source = row[11]
    post_date = row[13]

    r = requests.get(api_url + post_id, params=payload)

    # retrieve new video or picture url as these expire after some time
    if type in ['VIDEO', 'PHOTO']:
        source = r.json().get('source')
        picture = r.json().get('full_picture')

    post = {'text': row[0], 'num_likes': row[1], 'num_shares': row[2], 'num_angry': row[3], 'num_haha': row[4],
            'num_wow': row[5], 'num_love': row[6], 'num_sad': row[7], 'name': row[8], 'type': type,
            'picture': picture, 'source': source, 'perm_link': row[12], 'date': post_date, 'paid': row[14],
            'owner': row[15], 'id': post_id}
    cursor.execute('SELECT text, id, parent_id, date from comment where post_id ="' + post_id + '"')
    # add comments
    post['comments'] = []
    comments = cursor.fetchall()

    tree = build_tree(comments)
    sort_tree(tree)

    post['comments'] = tree

    post['num_comments'] = len(post['comments'])
    cursor.execute('SELECT id, name FROM category_name')
    category_names = cursor.fetchall()
    # close database connection
    mariadb_connection.close()

    # reactions became globally active on february the 24th in 2016
    reactions_available = post_date >= datetime.strptime('2016-02-24', "%Y-%m-%d")
    work_time = datetime.now()
    info = {"reactions_available": reactions_available,
            "work_time": work_time}

    # return post page
    return render_template('post.html', post=post, category_names=category_names, info=info)


@app.route('/update', methods=['POST'])
@auth.login_required
def update():
    # Read form from request
    cat = request.form.get("category", None)
    succ = request.form.get('success', None)
    sentiment = request.form.get('sentiment', None)
    id = request.form["post_id"]
    duration_seconds = (
        datetime.now() - datetime.strptime(request.form["work_time"], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()
    error = 0

    # Validation checks
    if cat is None:
        flash('Bitte wählen Sie eine Kategorie aus.')
        error = 1
    if succ is None:
        flash('Bitte wählen Sie aus, ob dieser Post erfolgreich war oder nicht.')
        error = 1
    if sentiment is None:
        flash('Bitte wählen Sie aus, ob die Stimmung aller Kommentare positiv, neutral oder negativ ist.')
        error = 1

    if error == 1:
        return redirect(url_for('getpost', post_id=id))

    # Build statements
    stmt = "REPLACE INTO category(user, post_id, category_name_id, sentiment, successful, duration_seconds) VALUES(%s, %s, %s, %s, %s, %s)"

    # Update Record in Database
    print('Updating record ' + str(id))
    connection = get_db_connection()
    cursor = connection.cursor(buffered=True)
    cursor.execute(stmt, (auth.username(), id, cat, sentiment, succ, duration_seconds))
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
