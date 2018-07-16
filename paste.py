from flask import Flask, render_template, g, abort

import db
import timer
import api

app = Flask(__name__)
app.config.from_object('config.Default')
app.register_blueprint(api.api, url_prefix='/api')

db_class = db.DB()

# init plugins
db_class.init_app(app)
timer.init_app(app)

days_opt = {
    3: '三天',
    7: '一周',
    14: '两周'
}


@app.route('/')
@app.route('/new/')
def new():
    langs = g.db.query_lang_all()
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
    post = g.db.query_post_one(post_id=post_id)
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
