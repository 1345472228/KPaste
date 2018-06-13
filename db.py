import datetime

import markdown
from flask import g
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy import create_engine, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

with open('./sqlurl.txt') as f:
    engine = create_engine(f.readline(), echo=False)

Base = declarative_base()

Post_form_require_items = ('title', 'author', 'language_id', 'validity_days',
                           'rawcontent', 'other')
days_opt = {
    3: 'Three days',
    7: 'A week',
    14: 'Fortnight'
}


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
    language_id = Column(Integer, ForeignKey('language.id'))

    # language = relationship("Language", backref="post")

    column_tuple = ('id', 'title', 'other', 'author', 'rawcontent', 'html',
                    ('datetime', str), 'validity_days', 'language_id',
                    ('language', lambda obj: obj and obj.to_dict())
                    )

    def to_dict(self):
        d = {}
        for colname in self.column_tuple:
            func = None
            if isinstance(colname, (tuple, list)):
                col = getattr(self, colname[0], None)
                func = colname[1]
                colname = colname[0]
            else:
                col = getattr(self, colname, None)
            if func:
                col = func(col)
            d[colname] = col
        return d

    def __repr__(self):
        return "<Post(id={}, title='{}', author={}, language_id={}, datetime={}, validity_days={})>". \
            format(self.id, self.title, self.author, self.language_id, self.datetime, self.validity_days)

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
    def __init__(self):
        self.ScopedSession = scoped_session(sessionmaker(bind=engine))
        self._session = None
        self.Post = Post
        self.Language = Language

    def init_app(self, app):
        @app.before_request
        def add_db_to_g():
            g.db = self

        @app.teardown_request
        def close_db(exception=None):
            self.close_session()

        app.database = self

    @property
    def session(self):
        if self._session is None:
            self._session = self.ScopedSession()
        return self._session

    def close_session(self):
        self.ScopedSession.remove()
        self._session = None

    def add_post(self, rawcontent, language, datetime=None,
                 validity_days=None, title=None, author=None, other=None,
                 **kwargs):

        if isinstance(language, int):
            lang_obj = self.query_lang(language)
        elif isinstance(language, Language):
            lang_obj = language
        else:
            raise TypeError("Unexcepted type of language: {}".format(type(language)))

        if not lang_obj:
            # Log here
            raise IndexError("No Such Language")
        else:
            html = self.raw2html(rawcontent, lang_obj.name)
            new_post = Post(title=title, rawcontent=rawcontent, html=html,
                            other=other, datetime=datetime, validity_days=validity_days,
                            author=author)
            new_post.language = lang_obj
            try:
                self.session.commit()
                return new_post
            except:
                self.session.rollback()
                raise IOError('Add post: commit failed')

    def raw2html(self, raw, lang):
        md = '```\n:::{} \n{}\n```\n'.format(lang, raw)
        return markdown.markdown(md, ["nl2br", "codehilite(linenums=True)", "extra"])

    def query_post_all(self):
        return self.session.query(Post, Language). \
            outerjoin(Language)

    def query_post_one(self, post_id):
        return self.session.query(Post, Language). \
            outerjoin(Language). \
            filter(Post.id == post_id).one_or_none()

    def update_post(self, post_obj, form):
        post_obj.update(form)
        if 'rawcontent' in form:
            post_obj.html = self.raw2html(form['rawcontent'], post_obj.language.name)

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return post_obj.id

    def add_language(self, lang_name):
        lang = Language(name=lang_name)
        try:
            self.session.add(lang)
            self.session.commit()
            return lang
        except Exception as e:
            self.session.rollback()
            raise e

    def query_lang(self, lang_id, q_all=False):
        if q_all:
            return self.session.query(Language)
        else:
            return self.session.query(Language).filter(Language.id == lang_id).one_or_none()

    def delete(self, obj):
        if isinstance(obj, Base):
            try:
                self.session.delete(obj)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise e
        else:
            raise TypeError('delete require a Base instance, but got a ' + type(obj))

    def check_validity(self):
        for q in self.query_post_all(0):
            if q.Post.is_expired():
                try:
                    self.session.delete(q.Post)
                    self.session.commit()
                    print("deleted {}", q.Post)
                    return True
                except Exception as e:
                    self.session.rollback()
                    raise e
            else:
                return False

    def pagiate(self, page, per_page):
        return self.session.query(Post).offset((per_page-1)*page).limit(per_page)

if __name__ == "__main__":
    Base.metadata.create_all(engine)

    db = DB()

    l1 = db.query_lang(19)
    l2 = db.query_lang(19)
    p1 = db.query_post_one(post_id=10)
    p1.Post.language_id = 19
    # db.session.add(new)
    db.session.commit()
