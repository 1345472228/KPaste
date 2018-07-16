import json

from flask import Blueprint, request, g, make_response, session

from exception import *

api = Blueprint('api', __name__)


# RESTful API

# error code
#   100         缺少参数
#   101         参数错误
#
#   200         无权限
#   201         未验证
#   202         access_key不正确
#
#   30x         未找到
#       301     未找到post
#       302     未找到language

def mkjson_error(msg, code, **kwargs):
    d = {'success': False, 'error': {'message': msg, 'code': code}}
    d.update(**kwargs)
    return json.dumps(d, indent=4)


def mkjson_success(data, **kwargs):
    d = None
    if data is None:
        d = {'success': True, }
    else:
        d = {'success': True, 'data': data}
    d.update(**kwargs)
    return json.dumps(d, indent=4)


json_header = {'Content-type': 'application/json'}


def isAuthorizedFor(post_id):
    '''查看此用户对post是否经过验证'''
    return session.get(str(post_id)) == 'true'


@api.route('/authorized/<int:post_id>/', methods=['POST'])
def authorized(post_id):
    return make_response(
        # succeed_info.format('authorized', 'true' if isAuthorizedFor(post_id) else 'false'),
        mkjson_success(data={'authorized': isAuthorizedFor(post_id)}),
        json_header
    )


@api.route('/authorize/', methods=['POST'])
def authorize():
    form = request.form
    post_id = form.get('post_id')
    access_key = form.get('access_key')
    if post_id is None or access_key is None:
        return make_response(
            # error_info.format('error arguments'),
            mkjson_error('error argument', '100'),
            json_header
        )

    post = g.db.query_post_one(post_id)
    if post is None:
        return make_response(
            # error_info.format('No Such Post'),
            mkjson_error('no such post', '301'),
            json_header
        )

    succ = post.check_access_key(access_key)
    if not succ:
        return make_response(
            # error_info.format('error access key'),
            mkjson_error('error access key', '202'),
            json_header
        )

    session[post_id] = 'true'
    return make_response(
        # succeed_info.format('authorized', 'true'),
        mkjson_success(data={'authorized': True}),
        json_header
    )


@api.route('/post/', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        # 新建
        form = request.form.to_dict()
        err_list = g.db.Post.check_form(form)

        try:
            new_post = g.db.add_post(form)
        except ArgRequireError as arg_list:
            err_msg = 'require argment(s): ' + ';'.join(err_list)
            return make_response(
                mkjson_error(err_msg, '100'),
                json_header
            )
        except NoSuchLangError as lang_id:
            return make_response(
                mkjson_error('no such language[language_id: {}]'.format(lang_id), 302),
                json_header
            )

        return make_response(
            # succeed_info.format('post_id', new_post.id),
            mkjson_success(data={'post_id': new_post.id}),
            json_header
        )

    elif request.method == 'GET':
        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            return make_response(
                # error_info.format('error argument: page'),
                mkjson_error('error argument: page;', 101),
                json_header
            )
        try:
            per = int(request.args.get('perpage', 20))
        except ValueError:
            return make_response(
                mkjson_error('error argument: perpage;', 101),
                json_header
            )

        result = g.db.pagiate(page, per)
        post_list = list(map(lambda x: x.to_dict(), result))

        return make_response(
            mkjson_success(data=post_list),
            json_header
        )


@api.route('/post/<int:post_id>', methods=['GET', 'DELETE', 'PUT'])
def post_with_id(post_id):
    if request.method == 'GET':
        post = g.db.query_post_one(post_id=post_id)
        if post is None:
            return make_response(
                mkjson_error('no such post', 301),
                json_header
            )

        post_dict = post.to_dict()
        return make_response(
            mkjson_success(data=post_dict),
            json_header
        )

    elif request.method == 'PUT':
        access_key = request.form.get('access_key')
        post = g.db.query_post_one(post_id)

        if post is None:
            return make_response(
                mkjson_error('no such post', '301'),
                json_header
            )
        if not isAuthorizedFor(post_id) and not post.check_access_key(access_key):
            return make_response(
                mkjson_error('have not authorized', 200),
                json_header
            )

        form = request.form.to_dict()
        id, warning = g.db.update_post(post, form)

        return make_response(
            mkjson_success(data={'post_id': id, 'warning': warning}),
            json_header
        )

    elif request.method == 'DELETE':
        # 传递正确access_key或者经过验证才可以操作
        access_key = request.form.get('access_key')
        post = g.db.query_post_one(post_id)

        if post is None:
            return make_response(
                mkjson_error('no such post', 301),
                json_header
            )

        if not isAuthorizedFor(post_id) and not post.check_access_key(access_key):
            return make_response(
                mkjson_error('have not authorized', 200),
                json_header
            )

        g.db.delete(post)

        return make_response(
            mkjson_success(None),
            json_header
        )
