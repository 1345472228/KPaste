from flask import Blueprint, render_template, request, g, make_response
import json
from db import Post_form_require_items, days_opt

api = Blueprint('api', __name__)

# RESTful API
error_info = "{{\n\t'error': '{}'\n}}"
succeed_info = "{{\n\t'succeed': 1,\n'info': '{}'\n}}"


@api.route('/post/<int:post_id>', methods=['GET', 'POST', 'DELETE'])
def post(post_id):
    if request.method == 'GET':
        postandlang = g.db.query_post(post_id=post_id)
        if postandlang is None:
            return make_response(
                error_info.format('no such post'),
                404,
                {'Content-type': 'application/json'}
            )
        else:
            post_dict = postandlang.Post.to_dict()
            post_dict.update({'succeed': 1})
            return make_response(
                json.dumps(post_dict, indent=4),
                {'Content-type': 'application/json'}
            )
    elif request.method == 'POST':
        pass
    elif request.method == 'DELETE':
        postandlang = g.db.query_post(post_id=post_id)
        if postandlang is None:
            return make_response(
                error_info.format('no such post'),
                404,
                {'Content-type': 'application/json'}
            )
        else:
            g.db.session.delete(postandlang.Post)
            return make_response(
                succeed_info.format('deleted'),
                226,
                {'Content-type': 'application/json'}
            )


@api.route('/post/new/', methods=['GET', 'POST'])
def post_new():
    if request.method == 'GET':
        langs = g.db.query_lang(lang_id=0, q_all=True)
        return render_template('new.html', languages=langs, days_opt=days_opt)

    elif request.method == 'POST':
        form = request.form.to_dict()
        print(form)
        for x in Post_form_require_items:
            if form.get(x, None) is None:
                return make_response(
                    error_info.format('require argment ' + x),
                    406,
                    {'Content-type': 'application/json'}
                )

        lang = g.db.query_lang(lang_id=form['language_id'])
        if lang is None:
            return make_response(
                error_info.format('not a correct language_id'),
                406,
                {'Content-type': 'application/json'}
            )
        else:
            new_post = g.db.add_post(**form, language=lang)
            return make_response(
                "{{'post_id': {}}}".format(new_post.id),
                {'Content-type': 'application/json'}
            )

