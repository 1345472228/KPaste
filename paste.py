from flask import Flask, url_for, redirect, render_template, request, g, abort, session, make_response

import db
import timer
import api
import logger

app = Flask(__name__)
app.config.from_object('config.Default')
app.register_blueprint(api.api, url_prefix='/api')

logger.init_app(app)
db = db.DB()
db.init_app(app)

timer.init_db(db)
app.add_url_rule('/timer/begin/', None, timer.begin)
app.add_url_rule('/timer/stop/', None, timer.stop)

days_opt = {
    3: '三天',
    7: '一周',
    14: '两周'
}


@app.route('/')
@app.route('/new/')
def new():
    langs = db.query_lang_all()
    return render_template('new.html', languages=langs, days_opt=days_opt, default_lang='c')


@app.route('/edit/<int:post_id>/')
def edit(post_id):
    if not api.isAuthorizedFor(post_id):
        abort(403)

    post = g.db.query_post_one(post_id)
    if post is None:
        abort(404)

    langs = g.db.query_lang_all()
    return render_template('edit.html', post=post, languages=langs, days_opt=days_opt)


@app.route('/show/<int:post_id>/')
def show(post_id):
    post = db.query_post_one(post_id=post_id)
    if post:
        return render_template('show.html', post=post)
    else:
        abort(404)


@app.errorhandler(404)
def err404(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def err403(e):
    return render_template('403.html'), 403


if __name__ == '__main__':
    app.run()
