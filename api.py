import json

from flask import Blueprint, request, g, make_response

api = Blueprint('api', __name__)

# RESTful API
error_info = '''{{
    "error": "{}"
}}'''
succeed_info = '''{{
    "succeed": "1",
    "{}": "{}"
}}'''
json_header = {'Content-type': 'application/json'}


@api.route('/post/', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        # 没有传入id，新建
        form = request.form.to_dict()
        err = g.db.Post.check_form(form)
        if err is not None:
            return make_response(
                error_info.format('require argment ' + err),
                406,
                json_header
            )
        lang = g.db.query_lang(lang_id=form['language_id'])
        if lang is None:
            return make_response(
                error_info.format('not a correct language_id'),
                406,
                json_header
            )

        new_post = g.db.add_post(form, check_form=False, language=lang)
        return make_response(
            "{{\"post_id\": {}}}".format(new_post.id),
            json_header
        )
    elif request.method == 'GET':
        page = int(request.args.get('page', 1))
        per = int(request.args.get('perpage', 20))

        result = g.db.pagiate(page, per)
        # if result.first() is None:
        #     pass
        l = list(map(lambda x: x.to_dict(), result))
        d = {
            'succeed': '1',
            'result': l
        }

        return make_response(
            json.dumps(d, indent=4),
            json_header
        )


@api.route('/post/<int:post_id>', methods=['GET', 'DELETE', 'PUT'])
def post_id(post_id):
    if request.method == 'GET':
        postandlang = g.db.query_post_one(post_id=post_id)
        if postandlang is None:
            return make_response(
                error_info.format('no such post'),
                404,
                json_header
            )

        post_dict = postandlang.Post.to_dict()
        post_dict.update({'succeed': '1'})
        post_dict.pop('access_key')
        return make_response(
            json.dumps(post_dict, indent=4),
            json_header
        )

    elif request.method == 'PUT':
        access_key = request.form.get('access_key')
        print(access_key)
        if  access_key is None:
            return make_response(
                error_info.format('access_key required'),
                401,
                json_header
            )

        postandlang = g.db.query_post_one(post_id=post_id)
        if postandlang is None:
            return make_response(
                error_info.format('No such post'),
                404,
                json_header
            )

        print(access_key)
        if not postandlang.Post.check_access_key(access_key):
            return make_response(
                error_info.format('access_key not correct'),
                401,
                json_header
            )

        form = request.form.to_dict()
        id = g.db.update_post(postandlang.Post, form)
        return make_response(
            succeed_info.format(post_id, id),
            json_header
        )

    elif request.method == 'DELETE':
        # 传递正确access_key才可以操作

        access_key = request.form.get('access_key')
        print(access_key)
        if  access_key is None:
            return make_response(
                error_info.format('access_key required'),
                401,
                json_header
            )

        postandlang = g.db.query_post_one(post_id=post_id)
        if postandlang is None:
            return make_response(
                error_info.format('No such post'),
                404,
                json_header
            )

        print(access_key)
        if not postandlang.Post.check_access_key(access_key):
            return make_response(
                error_info.format('access_key not correct'),
                401,
                json_header
            )

        g.db.delete(postandlang.Post)
        return make_response(
            succeed_info.format('info', 'deleted'),
            226,
            json_header
        )
