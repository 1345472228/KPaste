import datetime
import markdown
from sqlalchemy import create_engine, ForeignKey, func
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

with open('./sqlurl.txt') as f:
    engine = create_engine(f.readline(), echo=False)

# engine = create_engine("sqlite:///memory:")
Base = declarative_base()


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    title = Column(String(40), default="Untitled")
    other = Column(String(40), default="")
    author = Column(String(20), default="Unnamed")
    rawcontent = Column(Text, default="\n")
    html = Column(Text, default='')
    datetime = Column(TIMESTAMP, server_default=func.now())
    validity_days = Column(Integer, server_default='3')
    language_id = Column(Integer, ForeignKey('language.id'))

    language = relationship("Language", back_populates="post")

    def __repr__(self):
        return "<Post(id={}, title='{}', author={}, language_id={}, datetime={}, validity_days={})>".\
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

    post = relationship("Post", back_populates="language")

    def __repr__(self):
        return "<Language(id={}, name='{}')>".\
            format(self.id, self.name)

class DB():
    session = None
    # PostWithLang = namedtuple('PostWithLang', ['Post', 'Language'])
    languages = []

    def __init__(self, sessionmaker):
        self.session = sessionmaker()
        self.language = list(self.query_lang(0, q_all=True))

    def add_post(self, rawcontent, language, datetime=None,
                 validity_days=None, title=None, author=None, other=None,
                 **keyargs):

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
            md = '```\n:::{} \n{}\n```\n'.format(lang_obj.name, rawcontent)
            html = markdown.markdown(md, ["nl2br", "codehilite(linenums=True)", "extra"])
            new_post = Post(title=title, rawcontent=rawcontent, html=html,
                            other=other, datetime=datetime, validity_days=validity_days,
                            author=author)
            new_post.language = lang_obj
            try:
                self.commit()
                return new_post
            except:
                self.session.rollback()
                raise IOError('Add post: commit failed')

    def query_post(self, post_id, q_all=False):
        try:
            if q_all:
                return self.session.query(Post, Language). \
                    outerjoin(Language)
            else:
                return self.session.query(Post, Language). \
                    outerjoin(Language). \
                    filter(Post.id == post_id).one_or_none()
        except:
            raise IOError("Query post Failed")

    def add_language(self, lang_name):
        lang = Language(name=lang_name)
        try:
            self.session.add(lang)
            self.commit()
            return lang
        except:
            self.session.rollback()
            raise IOError("Add language Failed")

    def query_lang(self, lang_id, q_all=False):
        if q_all:
            return self.session.query(Language)
        else:
            return self.session.query(Language).filter(Language.id == lang_id).one_or_none()

    def commit(self):
        self.session.commit()

    def expired_and_del(self, post):
        if post.is_expired():
            try:
                self.session.delete(post)
                self.session.commit()
                print("deleted {}", post)
                return True
            except:
                self.session.rollback()
                raise IOError('Delete Failed')
        else:
            return False

    def check_validity(self):
        for q in self.query_post(0, q_all=True):
            self.expired_and_del(q.Post)

Base.metadata.create_all(engine)

if __name__ == "__main__":
    db = DB(sessionmaker(bind=engine))

    # p1 = Post(title="huffman", language_id=1)
    # p2 = Post(title='安徽')
    # l1 = Language(name="c")
    # l2 = Language(name="bash")
    # l3 = Language(name="Plain")
    # p1.language = l1
    # p2.language = l2

    # db.session.add_all([l1, l2, l3])
    # db.add_post(title="哈哈哈", rawcontent="", language=l1, datetime=datetime.datetime(2018, 5, 1), author=None)
    # db.add_post(title="嘿嘿嘿", rawcontent="#! /bin/bash", language=l2, author=None)

    # db.commit()
    for q in db.query_lang(0, q_all=True):
        db.session.delete(q)
    db.commit()
    with open('languages.txt') as f:
        tmp = f.readlines()
    langs = []
    for x in tmp:
        langs.append(Language(name=x.replace('\n', '')))
    print(langs)

    db.session.add_all(langs)
    db.commit()

    db.check_validity()
