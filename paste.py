from flask import Flask, url_for, redirect, render_template, flash, request, g
import DB
import threading
from datetime import timedelta

app = Flask(__name__)
session_func = DB.sessionmaker(bind=DB.engine)
db = DB.DB(session_func)

expired_check_timer = None
def expired_check_timer_handler(db):
    global expired_check_timer
    expired_check_timer = threading.Timer(timedelta(1).total_seconds(), expired_check_timer_handler)
    expired_check_timer.start()
    db.check_validity()

@app.route('/canceltimer')
def cancel_timer():
    try:
        if expired_check_timer and expired_check_timer.is_alive():
            expired_check_timer.cancel()
            return 'timer canceled'
        else:
            return 'timer has not started'
    except:
        return "Canceltimer: some errors occured"

@app.route('/starttimer')
def start_timer():
    try:
        if not expired_check_timer or not expired_check_timer.is_alive():
            expired_check_timer_handler(db)
            print('timer started')
            return 'timer started'
        else:
            print('timer has been alive')
            return 'timer has been alive'
    except Exception as e:
        print('[Start timer: some errors occured ]{}'.format(str(e)))
        return 'Start timer: some errors occured<br \>' + str(e)

start_timer()

@app.route('/')
@app.route('/new/')
def new():
    days_opt = {
        1: 'one day',
        3: 'three days',
        7: 'one week',
        14: 'one fortnight'
    }
    langs = db.query_lang(lang_id=0, q_all=True)
    return render_template('new.html', languages=langs, days_opt=days_opt)

@app.route('/show/')
@app.route('/show/<int:post_id>')
def show(post_id=None):
    if post_id:
        PostAndLang= db.query_post(post_id=post_id)
        if PostAndLang:
            return render_template('show.html', PostAndLang=PostAndLang)
        else:
            return "No Such Post"
    else:
        return "Error post_id"

@app.route('/create', methods=["POST"])
def create():
    form = request.form.to_dict()
    try:
        form['language'] = int(form['language'])
    except:
        return 'Error form'
    lang = db.query_lang(form['language'])
    if lang:
        newpost = db.add_post(**form)
        db.commit()
        return redirect(url_for('show', post_id=newpost.id))

if __name__ == '__main__':
    app.run(debug=True)
