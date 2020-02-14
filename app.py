import ast
import os
import logging

import mysql.connector as mariadb
import requests
from datetime import datetime
from flask import Flask, render_template, flash, abort
from flask import redirect
from flask import request
from flask import url_for
from flask_httpauth import HTTPBasicAuth
from flask import Markup
from tree import build_tree, sort_tree

from config import db_host, db_port, db_user, db_password, db_name, users, secret_key

app = Flask(__name__)
auth = HTTPBasicAuth()
app.secret_key = secret_key

query_posts_classified = 'SELECT count(distinct p.post_id), count(distinct c.post_id), round(count(distinct c.post_id)/count(distinct p.post_id)*100,2) FROM post_has_phase p LEFT JOIN category c on (p.post_id = c.post_id) WHERE c.user IS NULL OR c.user NOT IN ("ben","max")'


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
    try:
        mariadb_connection = get_db_connection()
        cursor = mariadb_connection.cursor(buffered=True)
        cursor.execute(
            query_posts_classified)
        if cursor.rowcount != 0:
            row = cursor.fetchone()
            total = row[0]
            current = row[1]
            percent = row[2]

        statistic = {"total": total,
                     "current": current,
                     "percent": percent}
        return render_template('index.html', statistic=statistic)
    finally:
        # close database connection
        mariadb_connection.close()


@app.route('/statistics')
@auth.login_required
def statistics():
    total = 0
    current = 0
    percent = 0
    current_user = 0
    try:
        mariadb_connection = get_db_connection()
        cursor = mariadb_connection.cursor(buffered=True)
        cursor.execute(
            query_posts_classified)
        if cursor.rowcount != 0:
            row = cursor.fetchone()
            total = row[0]
            current = row[1]
            percent = row[2]

        cursor.execute(
            'SELECT count(distinct c.post_id) FROM post p LEFT JOIN category c on (p.id = c.post_id) WHERE c.user = %s', (auth.username(),))
        if cursor.rowcount != 0:
            row = cursor.fetchone()
            current_user = row[0]

        statistic = {"total": total,
                     "current": current,
                     "percent": percent,
                     "current_user": current_user,
                     "username": auth.username()}
        return render_template('statistics.html', statistic=statistic)
    finally:
        # close database connection
        mariadb_connection.close()


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/phase/<phase_id>/generate')
@auth.login_required
def generate(phase_id):
    try:
        mariadb_connection = get_db_connection()
        cursor = mariadb_connection.cursor(buffered=True)

        if int(phase_id) == 0:
            cursor.execute('SELECT post_id FROM post_has_phase WHERE phase_id = 0 AND post_id '
                           'NOT IN (SELECT post_id FROM category) AND '
                           'NOT EXISTS (SELECT post_id FROM post_has_phase '
                           'WHERE phase_id = 2 AND post_id '
                           'NOT IN (SELECT post_id FROM category WHERE user = %s)) ORDER BY rand() LIMIT 1',
                           (auth.username(),))
        else:
            cursor.execute('SELECT id FROM post WHERE id NOT IN (SELECT post_id FROM category ' +
                           'WHERE user = %s) ' +
                           'AND id IN (SELECT post_id FROM post_has_phase ' +
                           'WHERE phase_id = %s) ' +
                           'ORDER BY rand() LIMIT 1', (auth.username(), str(phase_id)))

        if cursor.rowcount == 0:
            if int(phase_id) == 0:
                # to begin with phase 3, the user has to has no incomplete posts in phase 2
                cursor.execute('SELECT post_id FROM post_has_phase WHERE phase_id = %s '
                               'AND post_id NOT IN '
                               '(SELECT post_id FROM category WHERE user = %s);', (str(2), auth.username()))
                if cursor.rowcount > 0:
                    return render_template('incomplete.html', phase=int(3), last_phase=int(2))
                # there are no more posts of phase 3
                else:
                    return render_template('alldone.html', phase_id=int(phase_id))
            else:
                return render_template('alldone.html', phase_id=int(phase_id))
        else:
            rows = cursor.fetchone()
            post_id = rows[0]
            return redirect(url_for('getpost', phase_id=int(phase_id), post_id=post_id))
    finally:
        # close database connection
        mariadb_connection.close()


@app.route('/phase/<phase_id>/post/<post_id>')
@auth.login_required
def getpost(phase_id, post_id):
    try:
        # open database connection
        mariadb_connection = get_db_connection()

        # get post info from the database
        cursor = mariadb_connection.cursor(buffered=True)
        cursor.execute(
            'SELECT p.id, p.text FROM post p WHERE p.id = %s',
            (post_id,))
        if cursor.rowcount == 0 or cursor.rowcount > 1:
            abort(404)
        row = cursor.fetchall()[0]

        post_id_db = row[0]
        text = row[1]

        post_url = 'https://twitter.com/anyuser/statuses/' + post_id
        # dnt = do not track
        payload = {'url': post_url, 'lang': 'en', 'dnt': 'true'}
        r = requests.get('https://publish.twitter.com/oembed', params=payload)

        embed_tweet_html = Markup(r.json().get('html'))

        post = {'text': text, 'id': post_id, 'embed_tweet_html': embed_tweet_html}

        # fetch category names
        cursor.execute('SELECT id, name FROM category_name')
        category_names = cursor.fetchall()

        work_time = datetime.now()
        info = {"work_time": work_time}

        # return post page
        return render_template('post.html', post=post, category_names=category_names, info=info, phase_id=phase_id)
    finally:
        # close database connection
        mariadb_connection.close()


@app.route('/update', methods=['POST'])
@auth.login_required
def update():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(buffered=True)

        # Read form from request
        cat = request.form.getlist("category", None)
        id = request.form["post_id"]
        phase_id = request.form["phase_id"]
        duration_seconds = (
            datetime.now() - datetime.strptime(request.form["work_time"], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        # Build statements
        stmt = "REPLACE INTO category(user, post_id, duration_seconds) VALUES(%s, %s, %s)"
        stmt2 = "DELETE FROM category_has_category_name WHERE user = %s AND post_id = %s"
        stmt3 = "INSERT INTO category_has_category_name(user, post_id, category_name_id) VALUES(%s, %s, %s)"

        # Update Record in Database
        logging.debug('Updating record ' + str(id))
        cursor.execute(stmt, (auth.username(), id, duration_seconds))
        cursor.execute(stmt2, (auth.username(), id))
        for category_id in cat:
            cursor.execute(stmt3, (auth.username(), id, category_id))
        connection.commit()

        # Return to generate page for a new post
        return generate(phase_id)
    finally:
        # close database connection
        connection.close()


@app.route('/skip', methods=['POST'])
@auth.login_required
def skip():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(buffered=True)

        # Read form from request
        id = request.form["post_id"]
        phase_id = request.form["phase_id"]
        duration_seconds = (
            datetime.now() - datetime.strptime(request.form["work_time"], "%Y-%m-%d %H:%M:%S.%f")).total_seconds()

        # Build statements
        stmt = "REPLACE INTO skip(user, post_id, duration_seconds) VALUES(%s, %s, %s)"

        # Update Record in Database
        print('Skipping post ' + str(id))
        cursor.execute(stmt, (auth.username(), id, duration_seconds))
        connection.commit()

        # Return to generate page for a new post
        return generate(phase_id)
    finally:
        # close database connection
        connection.close()


# Private getter to create a connection object
def get_db_connection():
    return mariadb.connect(host=db_host, port=db_port, user=db_user, password=db_password,
                           database=db_name)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)  # NOSONAR
