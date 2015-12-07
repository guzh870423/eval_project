from flask import Flask, flash, render_template, url_for, request, redirect, session
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker
from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation, EvalForm, EvalListForm
from ConfigParser import SafeConfigParser
from encrypt import EvalCipher
from highcharts import Highchart
from itertools import groupby
from sqlalchemy import func, and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists
from wtforms.validators import DataRequired
from wtforms import Form
from werkzeug.datastructures import MultiDict
import itertools

parser = SafeConfigParser()
parser.read('config.ini')
username = parser.get('login', 'username')
password = parser.get('login', 'password')
schema = parser.get('login', 'schema')
host = parser.get('login', 'host')
port = parser.get('login', 'port')

app = Flask(__name__)
app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'p532keyconfidential'

engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema) 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
dbSession = DBSession()

key = parser.get('security', 'key')
evalCipher = EvalCipher(key)

@app.route('/eval', methods=['GET', 'POST'])
def list_all():
   if not session['app_user']:
        return redirect(url_for('login'))
     
   app_user = session['app_user']
   if request.method == 'POST':
        form = EvalListForm(request.form)
        evals = []
        evaler = dbSession.query(Student).filter_by(user_name=form.evaluations[0]['evaler_id'].data).first()
        semester = dbSession.query(Semester).filter_by(year=2015, season='Fall', course_no='P532').first()
        for eval in form.evaluations:
            evalee = dbSession.query(Student).filter_by(user_name=eval['evalee_id'].data).first()
            evaluation = Evaluation(evaler=evaler, evalee=evalee, week=eval['week'].data, rank=eval['rank'].data, token=eval['tokens'].data, description=eval['description'].data, adjective=eval['adjective'].data, semester=semester)
            evals.append(evaluation)
        
        key = 'keyskeyskeyskeys'
        evalCipher = EvalCipher(key)

        for e in evals:
            encryptedEval = evalCipher.encryptEval(e)
            dbSession.add(encryptedEval)
        dbSession.commit()
        
        return render_template('eval-success.html', week=form.evaluations[0]['week'].data)

   max_week = dbSession.query(func.max(Groups.week).label('maxweek'))
   
   evaler = aliased(Group_Student)
   evalee = aliased(Group_Student)

   sub_groups = dbSession.query(Groups.week, Groups.id.label('GROUP_ID'), Group_Student.student_id).filter(Groups.id==Group_Student.group_id, Groups.week==max_week).subquery()

   sub_student_evals = dbSession.query(Groups.week, Groups.id, evaler.student_id.label('EVALER_ID'), evalee.student_id.label('EVALEE_ID')).filter(Groups.id==evaler.group_id, evaler.group_id==evalee.group_id, evaler.student_id<>evalee.student_id, evaler.student_id==app_user).order_by(Groups.week, evaler.student_id, evalee.student_id).subquery()

   current_evals = dbSession.query(sub_groups.c.week.label('WEEK'), sub_student_evals.c.EVALER_ID, sub_student_evals.c.EVALEE_ID).filter(sub_groups.c.week >= sub_student_evals.c.week, sub_groups.c.student_id == sub_student_evals.c.EVALER_ID).group_by(sub_groups.c.week.label('WEEK'), sub_student_evals.c.EVALER_ID, sub_student_evals.c.EVALEE_ID).order_by(sub_groups.c.week, sub_student_evals.c.EVALER_ID).subquery()
   
   form_evals = dbSession.query(current_evals.c.WEEK, current_evals.c.EVALEE_ID, Student.first_name, Student.last_name).join(Student, current_evals.c.EVALEE_ID==Student.user_name).order_by(current_evals.c.EVALEE_ID).all()
   
   evalData = {'evaluations': form_evals}
   form = EvalListForm(data=MultiDict(evalData))

   for x, y in itertools.izip(form_evals,form.evaluations):
      y.evalee_id.data = x.EVALEE_ID
      y.evaler_id.data = app_user
      y.week.data = x.WEEK

   return render_template(
       'eval.html',
       form = form)

@app.route('/', methods=['GET', 'POST'])       
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        app_user = request.form['username']
        app_user_pwd = request.form['password']
        users = dbSession.query(Student).all()
        isAuthentic = dbSession.query(exists().where(and_(Student.user_name==app_user, Student.login_key==app_user_pwd))).scalar()
        
        if isAuthentic != True:
            error = 'Invalid Credentials. Please try again.'
        else:
            session['app_user'] = app_user
            return redirect(url_for('list_all'))
    return render_template('index.html', error=error)
    
@app.route('/logout')
def logout():
    session.pop('app_user')
    flash('You have been logged out successfully')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'p532keyconfidential'
    app.run(host='0.0.0.0', port=8085)