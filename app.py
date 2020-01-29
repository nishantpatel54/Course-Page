from flask import Flask, flash, session, redirect, url_for, escape, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = b'abbas'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment3.db'
db = SQLAlchemy(app)


@app.route('/')
def index():
    if 'username' in session:
        session.pop('username', None)
        return redirect(url_for('login'))
    return redirect(url_for('login'))


@app.route('/send_feedback', methods=['GET', 'POST'])
def send_feedback():
    if 'username' in session:
        username = session['username']
        ty = session['type'] == 'instructor'
        iusername = request.form['username']
        feedback = request.form['feedback']
        date = datetime.today().strftime('%Y-%m-%d')
        query = """
        INSERT INTO feedbacks
        VALUES('{}','{}','{}')
        """.format(iusername, date, feedback)
        db.engine.execute(query)
        return render_template('index.html', data=session['data'], type=ty)
    else:
        return redirect(url_for('login'))


@app.route('/remark_sent', methods=['GET', 'POST'])
def remark():
    if 'username' in session:
        username = session['username']
        ty = session['type'] == 'instructor'
        reason = request.form['reason']
        event = request.form['event']
        query = """
        INSERT INTO remarks
        VALUES('{}','{}','{}')
        """.format(username, event, reason)
        db.engine.execute(query)
        return render_template('index.html', data=session['data'], type=ty)
    else:
        return redirect(url_for('login'))


@app.route('/change_marks', methods=['GET', 'POST'])
def change_marks():
    if 'username' in session:
        user = request.form['username']
        event = request.form['event']
        grade = request.form['grade']
        ty = session['type'] == 'instructor'
        change = """
        UPDATE marks
        SET {}='{}'
        WHERE username='{}'
        """.format(event, grade, user)
        db.engine.execute(change)

        instructor = """
        SELECT *
        FROM marks
        """
        data = db.engine.execute(instructor)
        marks = {}
        names = []
        for user in data:
            m = {}
            names.append(user.username)
            m.update({'midterm': user.midterm})
            m.update({'final': user.final})
            m.update({'assignment1': user.assignment1})
            m.update({'assignment2': user.assignment2})
            m.update({'assignment3': user.assignment3})
            marks.update({user.username: m})
        session['data'] = marks

        return render_template('index.html', data=session['data'], type=ty, feedback=session['feedback'], requests=session['requests'])
    else:
        return redirect(url_for('login'))


@app.route('/home')
def home():
    ty = session['type'] == 'instructor'
    if session['type'] == 'instructor':
        return render_template('index.html', type=ty)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sql = """
            SELECT *
            FROM users
            """
        results = db.engine.execute(text(sql))
        for result in results:
            if result['username'] == request.form['username']:
                if result['password'] == request.form['password']:
                    session['username'] = request.form['username']
                    session['type'] = result['type']
                    globalusername = session['username']
                    ty = session['type'] == 'instructor'
                    if session['type'] == 'student':
                        student = """
                        SELECT *
                        FROM marks
                        WHERE username='{}'
                        """.format(session['username'])
                        data = db.engine.execute(text(student))
                        m = {}
                        for marks in data:
                            m.update({'midterm': marks.midterm})
                            m.update({'final': marks.final})
                            m.update({'assignment1': marks.assignment1})
                            m.update({'assignment2': marks.assignment2})
                            m.update({'assignment3': marks.assignment3})
                        session['data'] = m
                        return render_template('index.html', data=session['data'], type=ty)
                    elif session['type'] == 'instructor':
                        #requests = {'username1': {'event1': 'reason1', 'event2': 'reason2'}, 'username2': {'event1': 'reason1', 'event2': 'reason2'}}
                        instructor = """
                        SELECT *
                        FROM marks
                        """
                        data = db.engine.execute(instructor)
                        marks = {}
                        names = []
                        for user in data:
                            m = {}
                            names.append(user.username)
                            m.update({'midterm': user.midterm})
                            m.update({'final': user.final})
                            m.update({'assignment1': user.assignment1})
                            m.update({'assignment2': user.assignment2})
                            m.update({'assignment3': user.assignment3})
                            marks.update({user.username: m})
                        session['data'] = marks

                        remarks = """
                        SELECT *
                        FROM remarks
                        """
                        m = db.engine.execute(text(remarks))
                        requests = {}
                        for user in m:
                            if user.username not in requests.keys():
                                requests.update({user.username: {user.event: user.reason}})
                            else:
                                requests[user.username].update({user.event: user.reason})
                        session['requests'] = requests

                        f_query = """
                        SELECT feedbacks.date,feedback
                        FROM feedbacks
                        WHERE username='{}'
                        """.format(session['username'])
                        temp = {}
                        r = db.engine.execute(text(f_query))
                        for f in r:
                            if f.date in temp.keys():
                                temp[f.date].append(f.feedback)
                            else:
                                temp.update({f.date: []})
                                temp[f.date].append(f.feedback)
                        session['feedback'] = temp
                        return render_template('index.html', data=session['data'], type=ty, feedback=session['feedback'], requests=session['requests'])

        flash("Incorrest password/username")
        return redirect(url_for('login'))
    elif 'username' in session:
        return redirect(url_for('index'))
    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    username = None
    password = None
    typesi = None
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            typesi = request.form['type'].lower()
            query = """
            INSERT INTO users
            VALUES('{}','{}','{}')
            """.format(username, password, typesi)
            db.engine.execute(text(query))
            if typesi == 'student':
                marks = """
                INSERT INTO marks
                VALUES('{}',NULL,NULL,NULL,NULL,NULL)
                """.format(username)
                db.engine.execute(marks)
        except IntegrityError:
            flash("Sorry this username is taken, try another one please!")
            redirect(url_for('register'))
    # error, there already is a user using this bank address or other
    # constraint failed
        return redirect(url_for('login'))
    else:
        return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
