from flask import Flask, url_for, redirect, render_template, request, g

import db
import timer
from api import api
from db import days_opt
import logger

app = Flask(__name__)
app.config.from_object('config.Debug')
app.register_blueprint(api, url_prefix='/api')

logger.init_app(app)
db = db.DB()
db.init_app(app)

timer.init_db(db)
app.add_url_rule('/timer/begin/', None, timer.begin)
app.add_url_rule('/timer/stop/', None, timer.stop)


@app.route('/')
@app.route('/new/')
def new():
    langs = db.query_lang(lang_id=0, q_all=True)
    return render_template('new.html', languages=langs, days_opt=days_opt)


@app.route('/show/')
@app.route('/show/<int:post_id>')
def show(post_id=None):
    if post_id:
        PostAndLang = db.query_post_one(post_id=post_id)
        if PostAndLang:
            return render_template('show.html', PostAndLang=PostAndLang)
        else:
            return "No Such Post"
    else:
        return "Error post_id"


if __name__ == '__main__':
    app.run()
