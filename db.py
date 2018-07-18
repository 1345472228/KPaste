import crypt
import datetime

import markdown
from flask import g
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy import create_engine, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

from exception import *


class Tools():
    @classmethod
    def raw2html(cls, raw, lang):
        md = '```\n:::{} \n{}\n```\n'.format(lang, raw)
        return markdown.markdown(md, ["nl2br", "codehilite(linenums=True)", "extra"])


import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    with open('./sqlurl.txt') as f:
        DATABASE_URL = f.readline()

engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(40), default="Untitled")
    other = Column(String(40), default="")
    author = Column(String(20), default="Unnamed")
    rawcontent = Column(Text, default="\n")
    html = Column(Text, default='')
    datetime = Column(TIMESTAMP, server_default=func.now())
    validity_days = Column(Integer, server_default='3')
    access_key = Column(String)
    language_id = Column(Integer, ForeignKey('language.id'))

    _create_column = (
        'title', 'other', 'author', 'rawcontent',
        'html', 'validity_days', 'language_id'
    )

    _to_dict_tuple = (
        'id', 'title', 'other', 'author', 'rawcontent', 'html',
        ('datetime', str),
        'validity_days',
        # 'access_key',
        'language_id',
        ('language', lambda obj: obj and obj.to_dict())
    )

    _update_allow = (
        'title', 'other', 'author', 'rawcontent', 'language_id'
    )

    # salt = b'$2b$12$aJF41CBAnEozj6ch82mrLe'
    salt = '$6$WJEhX4A0KtbIWKNl'
    _require_items = (
        'language_id',
        'rawcontent',
        'access_key'
    )

    @classmethod
    def createFromDict(cls, dict):
        d = {}
        for key in dict:
            if key in cls._create_column:
                d[key] = dict[key]
        return Post(**d)

    def set_access_key(self, key):
        self.access_key = crypt.crypt(key, self.salt)

    def check_access_key(self, inkey):
        try:
            inhash = crypt.crypt(inkey, self.salt)
        except:
            return False
        return inhash == self.access_key

    @classmethod
    def check_form(cls, form_dict):
        '''检查所需参数是否足够'''
        err = []
        for x in cls._require_items:
            if x not in form_dict:
                err.append(x)
        if err:
            raise ArgRequireError(', '.join(err))

    def update(self, form):
        warning = []
        for key, value in form.items():
            if key in self._update_allow:
                setattr(self, key, value)
            else:
                warning.append('{} cannot be updated')

        if 'rawcontent' in form:
            self.html = Tools.raw2html(form['rawcontent'], self.language.name)

        return warning

    def to_dict(self):
        d = {}
        for colname in self._to_dict_tuple:
            func = None
            if isinstance(colname, (tuple, list)):
                col = getattr(self, colname[0], None)
                func = colname[1]
                if func:
                    col = func(col)
                colname = colname[0]
            else:
                col = getattr(self, colname, None)
            d[colname] = col
        return d

    def __repr__(self):
        return "<Post(id={}, title='{}', author={}, language_id={}, " \
               "language={}, datetime={}, validity_days={})>". \
            format(self.id, self.title, self.author,
                   self.language_id, self.language,
                   self.datetime, self.validity_days
                   )

    def __str__(self):
        return "<Post(id={}, title='{}', author={}, language_id={}, " \
               "\language={}, datetime={}, validity_days={})>". \
            format(self.id, self.title, self.author,
                   self.language_id, self.language,
                   self.datetime, self.validity_days
                   )

    def is_expired(self):
        now_sec = datetime.datetime.now().timestamp()
        validity_sec = datetime.timedelta(self.validity_days).total_seconds()
        if self.datetime.timestamp() + validity_sec <= now_sec:
            return True
        else:
            return False


class Language(Base):
    __tablename__ = "language"

    id = Column(Integer, primary_key=True)
    name = Column(String(20))

    post = relationship("Post", backref="language")

    column_tuple = ('id', 'name')

    def to_dict(self):
        d = {}
        for colname in self.column_tuple:
            d[colname] = getattr(self, colname, None)
        return d

    def __repr__(self):
        return "<Language(id={}, name='{}')>". \
            format(self.id, self.name)


class DB():
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls.__init__(cls._instance)
        return cls._instance

    def __init__(self):
        self.ScopedSession = scoped_session(sessionmaker(bind=engine))
        self.Post = Post
        self.Language = Language

    def init_app(self, app):
        @app.before_request
        def add_db_to_g():
            g.db = self

        @app.teardown_request
        def close_db(exception=None):
            self.close_session()

        app._database = self

    @property
    def session(self):
        return self.ScopedSession()

    def close_session(self):
        self.ScopedSession.remove()

    def add_post(self, form, **kwargs):

        Post.check_form(form)

        lang_id = form.get('language_id')
        lang_obj = self.query_lang_one(lang_id=lang_id)
        if lang_obj is None:
            raise NoSuchLangError(lang_id)

        form['html'] = Tools.raw2html(form.get('rawcontent'), lang_obj.name)

        new_post = Post.createFromDict(form)
        new_post.set_access_key(form.get('access_key', ''))

        try:
            self.session.add(new_post)
            self.session.commit()
            return new_post
        except:
            self.session.rollback()
            raise

    def query_post_all(self):
        return self.session.query(Post, Language)

    def query_post_one(self, post_id):
        return self.session.query(Post). \
            filter(Post.id == post_id).one_or_none()

    def update_post(self, post, form):
        if post is None:
            raise NoSuchPostError

        try:
            form.pop('id')
            form.pop('validity_days')
        except:
            pass

        warning = post.update(form)

        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

        return post.id, warning

    def add_language(self, lang_name):
        lang = Language(name=lang_name)
        try:
            self.session.add(lang)
            self.session.commit()
            return lang
        except:
            self.session.rollback()
            raise

    _languages = None

    def refresh_lang_cache(self):
        languages = self.session.query(Language).all()
        id_list = map(lambda l: l.id, languages)
        self._languages = {lang_id: lang for lang_id, lang in zip(id_list, languages)}

    def query_lang_all(self, refresh=False):
        if refresh or self._languages is None:
            self.refresh_lang_cache()
        return self._languages.values()

    def query_lang_one(self, lang_id, refresh=False):
        if refresh or self._languages is None:
            self.refresh_lang_cache()
        try:
            lang_id = int(lang_id)
        except ValueError:
            return None
        return self._languages.get(lang_id, None)

    def delete(self, obj):
        if isinstance(obj, Base):
            try:
                self.session.delete(obj)
                self.session.commit()
            except:
                self.session.rollback()
                raise
        else:
            raise TypeError('delete require a Base instance, but got a ' + type(obj))

    autodelete_log = []

    def check_validity(self):
        for q in self.query_post_all():
            if q.Post.is_expired():
                self.autodelete_log.append(str(q))
                self.session.delete(q.Post)

        try:
            self.session.commit()
        except:
            self.session.rollback()

    def pagiate(self, page, per_page):
        return self.session.query(Post).offset((page - 1) * per_page).limit(per_page)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    d = DB()
    with open('languages.txt') as f:
        for x in f.readlines():
            d.session.add(Language(name=x.strip()))
        d.session.commit()
