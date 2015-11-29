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

weightsForAverageRank = []
for weight in parser.get('constants', 'weights_for_average_rank').split(','):
    weightsForAverageRank.append(int(weight))

app = Flask(__name__)

engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema) 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

key = parser.get('security', 'key')
evalCipher = EvalCipher(key)

@app.route('/main', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        year_season = request.form['semester']
        year = int(year_season.split(" ")[0])
        season = year_season.split(" ")[1]
        semester = session.query(Semester).filter_by(season=season, year=year).one()
        week=request.form['week']
        return redirect(url_for('reports', semester_id=semester.id, currentWeek=week))
    else:
        semesters = session.query(Semester).all()
  
        weeks = session.query(distinct(Groups.week)).all()
        return render_template('main.html', semesters=semesters, weeks=weeks, str=str)
@app.route('/chart', methods=['GET'])
def chart():
    # A chart is the container that your data will be rendered in, it can (obviously) support multiple data series within it.
    options = {
    'title': {
        'text': 'Normalized Rank Chart'
    },
    'subtitle': {
        'text': 'For student'
    },
    'xAxis': {
        'reversed': False,
        'title': {
            'enabled': True,
            'text': 'Rank'
        },
        'labels': {
            'formatter': 'function () {\
                return this.value;\
            }'
        },
        'maxPadding': 0.05,
        'showLastLabel': True
    },
    'yAxis': {
        'title': {
            'text': 'Week'
        },
        'labels': {
            'formatter': "function () {\
                return this.value;\
            }"
        },
        'lineWidth': 2
    },
    'legend': {
        'enabled': False
    },
    'tooltip': {
        'headerFormat': '<b>{series.name}</b><br/>',
        'pointFormat': 'Rank {point.x}: Week {point.y}'
    }
}
    chart = Highchart()
    chart.set_options('chart', {'inverted': True})
    chart.set_dict_options(options)    
    data = []
    averagedEval = session.query(Evaluation.evalee_id, Evaluation.week, func.avg(Evaluation.rank).label("avg")).filter_by(evalee_id='guzh').group_by(Evaluation.evalee_id, Evaluation.week).all()
          
    for eval in averagedEval:
       evalee = eval.evalee_id
       rank = round(eval.avg)
       week = eval.week
       
       points = [rank, week]
       data.append(points)    
       chart.add_data_set(data, 'spline', 'Normalized Rank', marker={'enabled': True}) 

    chart.save_file('templates/ranks')
    
    Evaluations = session.query(Evaluation).all()
    return render_template('chart.html',
        evals=Evaluations,
        averagedEval=averagedEval
      ) 
@app.route('/reports/<int:semester_id>/<int:currentWeek>', methods=['GET', 'POST'])
def reports(semester_id, currentWeek):
    semester = session.query(Semester).filter_by(id=semester_id).one()
    # list of students
    students = []
    # Evaluation dictionary: evals[currentWeek][evaler][evalee] = evaluation
    evals = []
    # normalized ranks dictionary: reversedEvals[Week][evalee][evaler][0] = evaluation
    #                              reversedEvals[Week][evalee][evaler][1] = normalized_rank
    #                              reversedEvals[Week][evalee][evaler][1] = normalized_token
    reversedEvals = []
    # sort evaler according to current week and rank
    sortedEvaler = []
    # average rank: averageRank[week][student]
    averageRank = []
    # average token: averageToken[week][student]
    averageToken = []
    # weighted rank
    weightedRank = {}
    
    enrollments = session.query(Enrollment).filter_by(semester_id=semester_id).all()
    for enrollment in enrollments:
        student = enrollment.student_id
        students.append(enrollment.student)
     
    # which weeks do two students work together, connection[student1][student2] = [week1, week2]
    connection = queryConnection(students)
    
    for week in range(1, currentWeek+1):
        evalsOneWeek, reversedEvalsOneWeek, sortedEvalerOneWeek, averageRankOneWeek, averageTokenOneWeek = queryEval(semester_id, week, students, connection)
        evals.append(evalsOneWeek)
        reversedEvals.append(reversedEvalsOneWeek)
        sortedEvaler.append(sortedEvalerOneWeek)
        averageRank.append(averageRankOneWeek)
        averageToken.append(averageTokenOneWeek)
    #sortedByAverageRank = sorted(averageRank, key=averageRank.get)
    #print sortedByAverageRank


                    
    # compute weighted average rank
    for evalee in reversedEvals[currentWeek-1]:
        weightedRank[evalee] = 0
        weightsSum = 0
        for evaler in reversedEvals[currentWeek-1][evalee]:
            rank = reversedEvals[currentWeek-1][evalee][evaler][1]
            weeks = connection[evalee][evaler]
            for week in weeks:                
                weightedRank[evalee] += rank * weightsForAverageRank[week-1]
                weightsSum += weightsForAverageRank[week-1]
        weightedRank[evalee] = round(weightedRank[evalee] / weightsSum, 3)

    return render_template('reports.html',
        semesterName=str(semester.year)+semester.season,
        currentWeek=currentWeek,
        students=students,
        connection=connection,
        evals=evals,
        reversedEvals=reversedEvals,
        sortedEvaler=sortedEvaler,
        averageRank=averageRank,
        averageToken=averageToken,
        len=len,
        weightedRank=weightedRank,
        )

# get connection matrix for students
def queryConnection(students):
    connection = {}
    #intialize connection
    for student1 in students:
        connection[student1.user_name] = {}
        for student2 in students:
            connection[student1.user_name][student2.user_name] = []
    
    #assign connection
    groups = session.query(Groups).all()
    for group in groups:
        studentsInGroup = session.query(Group_Student).filter_by(group_id=group.id).all()
        for student1 in studentsInGroup:
            for student2 in studentsInGroup:
                if student1 != student2:
                    connection[student1.student_id][student2.student_id].append(int(group.week))        
    return connection
                        
# query evaluation for one week        
def queryEval(semester_id, week, students, connection):
    # Evaluation dictionary: evalsOneWeek[evaler][evalee] = evaluation
    evalsOneWeek = {}
    # normalized ranks dictionary: reversedEvalsOneWeek[evalee][evaler][0] = evaluation
    #                           reversedEvalsOneWeek[evalee][evaler][1] = normalized_rank
    #                           reversedEvalsOneWeek[evalee][evaler][2] = normalized_token
    reversedEvalsOneWeek = {}
    # sort evaler according to current week and rank
    sortedEvalerOneWeek = {}
    # average rank
    averageRankOneWeek = {}
    # average token
    averageTokenOneWeek = {}
    for student in students:
        evaler = student.user_name
        evalsOneWeek[evaler] = {}
        evalsFromOneStudent = session.query(EncryptedEvaluation).filter_by(evaler_id=evaler, week=int(week), semester_id=semester_id).all()
        for encryptedEval in evalsFromOneStudent:
            eval = evalCipher.decryptEval(encryptedEval)
            evalee = eval.evalee_id
            evalsOneWeek[evaler][evalee] = eval
        
        for evalee, eval in evalsOneWeek[evaler].iteritems():
            if not reversedEvalsOneWeek.get(evalee):
                reversedEvalsOneWeek[evalee] = {}
            reversedEvalsOneWeek[evalee][evaler] = []
            reversedEvalsOneWeek[evalee][evaler].append(eval)
            reversedEvalsOneWeek[evalee][evaler].append(round(float(eval.rank) / len(evalsOneWeek[evaler]), 3))
            reversedEvalsOneWeek[evalee][evaler].append(eval.token * len(evalsOneWeek[evaler]))
    
    #sort evaler for each evalee
    for evalee in reversedEvalsOneWeek:
        sortedEvalerOneWeek[evalee] = []
        #sort by rank that evaler gives to evalee
        sortedByRank = sorted(reversedEvalsOneWeek[evalee].items(), key=lambda e: e[1][1])
        #put current team members top
        for item in sortedByRank:
            evaler = item[0]
            if week in connection[evalee][evaler]:
                sortedEvalerOneWeek[evalee].append(evaler)
        # non-current team members
        for item in sortedByRank:
            evaler = item[0]
            if week not in connection[evalee][evaler]:
                sortedEvalerOneWeek[evalee].append(evaler)
    
    for evalee in reversedEvalsOneWeek:
        averageRankOneWeek[evalee] = 0
        averageTokenOneWeek[evalee] = 0
        for evaler in reversedEvalsOneWeek[evalee]:
            rank = reversedEvalsOneWeek[evalee][evaler][1]
            token = reversedEvalsOneWeek[evalee][evaler][2]
            averageRankOneWeek[evalee] += rank / len(reversedEvalsOneWeek[evalee])
            averageTokenOneWeek[evalee] += token / len(reversedEvalsOneWeek[evalee])
    return evalsOneWeek, reversedEvalsOneWeek, sortedEvalerOneWeek, averageRankOneWeek, averageTokenOneWeek
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
    app.run(host='0.0.0.0', port=5000)
        