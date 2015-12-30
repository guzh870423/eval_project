from flask import Flask, flash, render_template, url_for, request, redirect, session
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker
from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation, EvalForm, EvalListForm, Manager_Eval
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

engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema, pool_recycle=28800) 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
dbSession = DBSession()

key = parser.get('security', 'key')
evalCipher = EvalCipher(key)

@app.route('/eval', methods=['GET', 'POST'])
def list_all():
    try:
        if not session['app_user']:
            return redirect(url_for('login'))
         
        app_user = session['app_user']
        if request.method == 'POST':
            form = EvalListForm()
            if form.validate_on_submit():
                key = 'keyskeyskeyskeys'
                evalCipher = EvalCipher(key)

                evals = []
                evaler = dbSession.query(Student).filter_by(user_name=form.evaluations[0]['evaler_id'].data).first()
                semester = dbSession.query(Semester).filter_by(year=2015, season='Fall', course_no='P532').first()
                for eval in form.evaluations:
                    evalee = dbSession.query(Student).filter_by(user_name=eval['evalee_id'].data).first()
                    
                    encryptedManagerEval = None
                    if eval['is_manager'].data == 1:
                        managerEval = Manager_Eval(approachable_attitude = eval['managerEval']['approachable'].data,
                                    team_communication = eval['managerEval']['communication'].data,
                                    client_interaction = eval['managerEval']['client_interaction'].data,
                                    decision_making = eval['managerEval']['decision_making'].data,
                                    resource_utilization = eval['managerEval']['resource_utilization'].data,
                                    follow_up_to_completion = eval['managerEval']['follow_up_to_completion'].data,
                                    task_delegation_and_ownership = eval['managerEval']['task_delegation_and_ownership'].data,
                                    encourage_team_development = eval['managerEval']['encourage_team_development'].data,
                                    realistic_expectation = eval['managerEval']['realistic_expectation'].data,
                                    performance_under_stress = eval['managerEval']['performance_under_stress'].data,
                                    mgr_description = 'None')
                                            
                        encryptedManagerEval = evalCipher.encryptManagerEval(managerEval)                    
                        dbSession.add(encryptedManagerEval)                    
                        
                    evaluation = Evaluation(evaler=evaler, evalee=evalee, week=eval['week'].data, rank=eval['rank'].data, token=eval['tokens'].data, description=eval['description'].data, adjective=eval['adjective'].data, encryptedManagerEval=encryptedManagerEval, semester=semester)
                    evals.append(evaluation)
                    
                for e in evals:
                    encryptedEval = evalCipher.encryptEval(e)
                    dbSession.add(encryptedEval)
                dbSession.commit()
                
                return render_template('eval-success.html', week=form.evaluations[0]['week'].data)           
            else:
                return render_template('eval.html',form = form)             
    except Exception as e:
            return render_template("error.html") 
            
    max_week = dbSession.query(func.max(Groups.week).label('maxweek'))
    number_of_evaluations_submitted = dbSession.query(EncryptedEvaluation).filter(EncryptedEvaluation.week == max_week, EncryptedEvaluation.evaler_id == app_user).count()
   
    if number_of_evaluations_submitted > 0:
        return render_template('resubmitError.html', week=max_week.scalar())
                
    evaler = aliased(Group_Student)
    evalee = aliased(Group_Student)

    sub_groups = dbSession.query(Groups.week, Groups.id.label('GROUP_ID'), Group_Student.student_id).filter(Groups.id==Group_Student.group_id, Groups.week==max_week).subquery()

    sub_student_evals = dbSession.query(Groups.week, Groups.id, evaler.student_id.label('EVALER_ID'), evalee.student_id.label('EVALEE_ID')).filter(Groups.id==evaler.group_id, evaler.group_id==evalee.group_id, evaler.student_id<>evalee.student_id, evaler.student_id==app_user).order_by(Groups.week, evaler.student_id, evalee.student_id).subquery()

    current_evals = dbSession.query(sub_groups.c.week.label('WEEK'), sub_student_evals.c.EVALER_ID, sub_student_evals.c.EVALEE_ID).filter(sub_groups.c.week >= sub_student_evals.c.week, sub_groups.c.student_id == sub_student_evals.c.EVALER_ID).group_by(sub_groups.c.week.label('WEEK'), sub_student_evals.c.EVALER_ID, sub_student_evals.c.EVALEE_ID).order_by(sub_groups.c.week, sub_student_evals.c.EVALER_ID).subquery()
   
    max_week_group_ids = dbSession.query(Groups.id).filter(Groups.week==max_week).subquery()
    current_managers = dbSession.query(Group_Student.student_id, Group_Student.is_manager).filter(Group_Student.group_id.in_(max_week_group_ids), Group_Student.is_manager==1).subquery()
   
    form_evals = dbSession.query(current_evals.c.WEEK, current_evals.c.EVALEE_ID, Student.first_name, Student.last_name, current_managers.c.is_manager).join(Student, current_evals.c.EVALEE_ID==Student.user_name).outerjoin(current_managers, current_evals.c.EVALEE_ID==current_managers.c.student_id).order_by(current_evals.c.EVALEE_ID).all()
   
    evalData = {'evaluations': form_evals}
    form = EvalListForm(data=MultiDict(evalData))

    for x, y in itertools.izip(form_evals,form.evaluations):
      y.evalee_id.data = x.EVALEE_ID
      y.evaler_id.data = app_user
      y.week.data = x.WEEK
      y.is_manager.data = x.is_manager

    return render_template(
       'eval.html',
       form = form)

@app.route('/', methods=['GET', 'POST'])       
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        try:
            app_user = request.form['username']
            app_user_pwd = request.form['password']
            users = dbSession.query(Student).all()
            isAuthentic = dbSession.query(exists().where(and_(Student.user_name==app_user, Student.login_pwd==app_user_pwd))).scalar()
            
            if isAuthentic != True:
                error = 'Invalid Credentials. Please try again.'
            else:
                session['app_user'] = app_user
                return redirect(url_for('list_all'))
        except Exception as e:
            return render_template("error.html")         
    return render_template('index.html', error=error)
    
@app.route('/logout')
def logout():
    session.pop('app_user')
    dbSession.close()
    flash('You have been logged out successfully')
    return redirect(url_for('login'))

@app.errorhandler
def page_not_found(e):
    return render_template('error.html')
    
if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'p532keyconfidential'
    app.run(host='0.0.0.0', port=8085)
