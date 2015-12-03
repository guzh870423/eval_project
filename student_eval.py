from flask import Flask, render_template, url_for, request, redirect
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker
from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation
from ConfigParser import SafeConfigParser
from encrypt import EvalCipher
from highcharts import Highchart
from itertools import groupby
from sqlalchemy import func, and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists

parser = SafeConfigParser()
parser.read('config.ini')
username = parser.get('login', 'username')
password = parser.get('login', 'password')
schema = parser.get('login', 'schema')
host = parser.get('login', 'host')
port = parser.get('login', 'port')

app = Flask(__name__)

engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema) 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

key = parser.get('security', 'key')
evalCipher = EvalCipher(key)

@app.route('/eval')
def list_all():
   max_week = session.query(func.max(Groups.week).label('maxweek'))
   
   evaler = aliased(Group_Student)
   evalee = aliased(Group_Student)

   sub_groups = session.query(Groups.week, Groups.id.label('GROUP_ID'), Group_Student.student_id).filter(Groups.id==Group_Student.group_id, Groups.week==max_week).subquery()

   sub_student_evals = session.query(Groups.week, Groups.id, evaler.student_id.label('EVALER_ID'), evalee.student_id.label('EVALEE_ID')).filter(Groups.id==evaler.group_id, evaler.group_id==evalee.group_id, evaler.student_id<>evalee.student_id, evaler.student_id==request.args['username']).order_by(Groups.week, evaler.student_id, evalee.student_id).subquery()

   current_evals = session.query(sub_groups.c.week.label('WEEK'), sub_student_evals.c.EVALER_ID, sub_student_evals.c.EVALEE_ID).filter(sub_groups.c.week >= sub_student_evals.c.week, sub_groups.c.student_id == sub_student_evals.c.EVALER_ID).group_by(sub_groups.c.week.label('WEEK'), sub_student_evals.c.EVALER_ID, sub_student_evals.c.EVALEE_ID).order_by(sub_groups.c.week, sub_student_evals.c.EVALER_ID).subquery()
   
   form_evals = session.query(current_evals.c.WEEK, current_evals.c.EVALEE_ID, Student.first_name, Student.last_name).join(Student, current_evals.c.EVALEE_ID==Student.user_name).order_by(current_evals.c.EVALEE_ID)

   return render_template(
       'eval.html',
       username = request.args['username'],
       form_evals=form_evals)

@app.route('/', methods=['GET', 'POST'])       
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        users = session.query(Student).all()
        isAuthentic = session.query(exists().where(and_(Student.user_name==username, Student.login_key==pwd))).scalar()
        print(isAuthentic)
        if isAuthentic != True:
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('list_all', username=username))
    return render_template('index.html', error=error)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)