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
import copy
import operator

round_digits = 3
tokenRange = 100
parser = SafeConfigParser()
parser.read('config.ini')
#username = parser.get('login', 'username')
#password = parser.get('login', 'password')
schema = parser.get('login', 'schema')
host = parser.get('login', 'host')
port = parser.get('login', 'port')

weightsForAverageRank = []
for weight in parser.get('constants', 'weights_for_average_rank').split(','):
    weightsForAverageRank.append(int(weight))

app = Flask(__name__)

#engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema) 
#Base.metadata.bind = engine
#DBSession = sessionmaker(bind=engine)
session = None #DBSession()

key = parser.get('security', 'key')
evalCipher = EvalCipher(key)

raw_options = {
    'chart':{
            'width': 1000,
            'height': 500,
    },
    'title':{
    },
    'xAxis': {
        'allowDecimals': False,
        'title': {
                'enabled': True,                
        },
        'labels': {
            'formatter': 'function () {\
                return this.value;\
            }'
        },
        'showLastLabel': True
    },
    'yAxis': {
        'reversed': True,
            'title': {
                
            },
            'labels': {
                'formatter': "function () {\
                    return this.value;\
                }"
            },
            'lineWidth': 2
    },
    'legend': {
            'enabled': True,
    },
        'tooltip': {
            'headerFormat': '<b>{series.name}</b><br/>',
            'pointFormat': 'Rank {point.x}: Week {point.y}'
        },
    'navigation':{
            'buttonOptions':{
                'enabled': False,
            }
    },
}
@app.route('/main', methods=['GET', 'POST'])
def main():
    if not session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        semester_id = request.form['semester']
        if request.form['submit'] == 'Get reports':
            week=request.form['week']
            return redirect(url_for('reports', semester_id=semester_id, currentWeek=week))
        elif request.form['submit'] == 'Set student alias_name':
            return redirect(url_for('set_alias', semester_id=semester_id))
        elif request.form['submit'] == 'Student drop class':
            return redirect(url_for('drop_class', semester_id=semester_id))
    else:
        semesters = session.query(Semester).all()
  
        weeks = session.query(distinct(Groups.week)).all()
        return render_template('main.html', semesters=semesters, weeks=weeks, str=str)

@app.route('/reports/<int:semester_id>/<int:currentWeek>', methods=['GET', 'POST'])
def reports(semester_id, currentWeek):
    if not session:
        return redirect(url_for('login'))
    semester = session.query(Semester).filter_by(id=semester_id).one()
    
    # list of students
    students = queryStudents(semester_id)
     
    # which weeks do two students work together, connection[student1][student2] = [week1, week2]
    connection = queryConnection(students)
    
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
    evals, reversedEvals, sortedEvaler, averageRank, averageToken = queryEvals(currentWeek, semester_id, students, connection)
    
    # sort students by unweighted average rank
    sortedByAverageRank = sorted(averageRank[currentWeek-1], key=averageRank[currentWeek-1].get)

    # names is a map from "user_name" to "alias_name" (if exists) or "first_name last_name" 
    names = mapNames(students)
    
    # students name list who fail to submit eval
    missingNames = missingEvalers(currentWeek, evals, students)
         
    # compute weighted average rank
    weightedRank = computeWeightedRanks(currentWeek, connection, reversedEvals, weightsForAverageRank)

    # generate performance trend comparison chart for all students
    compareChart(currentWeek, students, names, averageRank)
    # generate performance trend chart for each student 
    generateCharts(currentWeek, students, names, averageRank, averageToken)
    
    # most frequent adjective for each evalee, adjectives[evalee] = adjective
    adjectives = mostFrequentAdjectives(currentWeek, reversedEvals)
    
    return render_template('reports.html',
        semester=semester,
        currentWeek=currentWeek,
        students=students,
        sortedByAverageRank=sortedByAverageRank,
        names=names,
        missingNames=missingNames,
        connection=connection,
        evals=evals,
        reversedEvals=reversedEvals,
        sortedEvaler=sortedEvaler,
        averageRank=averageRank,
        averageToken=averageToken,
        len=len,
        weightedRank=weightedRank,
        adjectives=adjectives,
        )

# get list of students for specified semester
def queryStudents(semester_id):
    students = []
    enrollments = session.query(Enrollment).filter_by(semester_id=semester_id).all()
    for enrollment in enrollments:
        student = enrollment.student_id
        students.append(enrollment.student)
    return students
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
                        
# query evaluation for each week        
def queryEvalByWeek(semester_id, week, students, connection):
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
            numberOfEval = len(evalsOneWeek[evaler])
            reversedEvalsOneWeek[evalee][evaler].append(round((eval.rank - (numberOfEval + 1.0) / 2.0 ) / numberOfEval, round_digits))
            reversedEvalsOneWeek[evalee][evaler].append(eval.token * len(evalsOneWeek[evaler]) - tokenRange / 2)
    
    #sort evaler for each evalee
    for evalee in reversedEvalsOneWeek:
        sortedEvalerOneWeek[evalee] = []
        #sort by rank that evaler gives to evalee
        sortedByRank = sorted(reversedEvalsOneWeek[evalee].items(), key=lambda e: e[1][1])
        #put current team members top
        sortedEvalerOneWeek[evalee].append([])
        for item in sortedByRank:
            evaler = item[0]
            if week in connection[evalee][evaler]:
                sortedEvalerOneWeek[evalee][0].append(evaler)
        # non-current team members
        sortedEvalerOneWeek[evalee].append([])
        for item in sortedByRank:
            evaler = item[0]
            if week not in connection[evalee][evaler]:
                sortedEvalerOneWeek[evalee][1].append(evaler)
    
    for evalee in reversedEvalsOneWeek:
        flag = True
        for student in students:
            if student.user_name == evalee and not student.is_active:
                flag = False
                break
        if not flag:
            continue
        averageRankOneWeek[evalee] = 0
        averageTokenOneWeek[evalee] = 0
        for evaler in reversedEvalsOneWeek[evalee]:
            rank = reversedEvalsOneWeek[evalee][evaler][1]
            token = reversedEvalsOneWeek[evalee][evaler][2]
            averageRankOneWeek[evalee] += rank / len(reversedEvalsOneWeek[evalee])
            averageTokenOneWeek[evalee] += token / len(reversedEvalsOneWeek[evalee])
        averageRankOneWeek[evalee] = round(averageRankOneWeek[evalee], round_digits)
    
    return evalsOneWeek, reversedEvalsOneWeek, sortedEvalerOneWeek, averageRankOneWeek, averageTokenOneWeek

def queryEvals(currentWeek, semester_id, students, connection):
    evals = []
    reversedEvals = []
    sortedEvaler = []
    averageRank = []
    averageToken = []
    for week in range(1, currentWeek+1):
        evalsOneWeek, reversedEvalsOneWeek, sortedEvalerOneWeek, averageRankOneWeek, averageTokenOneWeek = queryEvalByWeek(semester_id, week, students, connection)
        evals.append(evalsOneWeek)
        reversedEvals.append(reversedEvalsOneWeek)
        sortedEvaler.append(sortedEvalerOneWeek)
        averageRank.append(averageRankOneWeek)
        averageToken.append(averageTokenOneWeek)
    return evals, reversedEvals, sortedEvaler, averageRank, averageToken

def compareChart(currentWeek, students, names, averageRank):
    options = copy.deepcopy(raw_options)
    options['title']['text'] = 'Normalized Rank Comparison Chart'
    options['yAxis']['title']['text'] = 'Normalized Rank'
    options['xAxis']['title']['text'] = 'Week'
    chart = Highchart()
    chart.set_dict_options(options)
    series = []
    
    for student in students:
        if not student.is_active:
            continue
        name = names[student.user_name]
        data = []
        for week in range(1, currentWeek + 1):
            rank = averageRank[week-1].get(student.user_name)
            if rank is not None:
                point = [week, rank]
                data.append(point)
        series.append({'name': name, 'data': data})
        chart.add_data_set(data, 'spline', name, marker={'enabled': True})
    #options['series'] = series
    chart.save_file('templates/charts/compare')

def generateCharts(currentWeek, students, names, averageRank, averageToken):
    options = copy.deepcopy(raw_options)
    options['yAxis'] = [{
        'reversed': True,
            'title': {
                'text': 'Normalized Rank'
            },
            'labels': {
                'formatter': "function () {\
                    return this.value;\
                }"
            },
            'lineWidth': 2
    },
    {
            'title': {
                'text': 'Normalized Token'
            },
            'labels': {
                'formatter': "function () {\
                    return this.value;\
                }"
            },
            'lineWidth': 2,
            'opposite': True
    },
    ]
    options['xAxis']['title']['text'] = 'Week'
    for student in students:
        if not student.is_active:
            continue
        chart = Highchart()
        options['title']['text'] = names[student.user_name]
        options['chart']['renderTo'] = 'container_' + student.user_name
        chart.set_dict_options(options)    
        rank_data = []
        token_data = []
        for week in range(1, currentWeek + 1):
            rank = averageRank[week-1].get(student.user_name)
            token = averageToken[week-1].get(student.user_name)
            if rank is not None and token is not None:
                point = [week, rank]
                rank_data.append(point)
                point = [week, token]
                token_data.append(point)
        chart.add_data_set(rank_data, 'spline', 'Normalized Rank', marker={'enabled': True})
        chart.add_data_set(token_data, 'spline', 'Normalized Token', marker={'enabled': True}, yAxis=1)
        chart.save_file('templates/charts/' + student.user_name)

def mapNames(students):
    names = {}
    for student in students:
        if student.alias_name:
            names[student.user_name] = student.alias_name
        else:
            names[student.user_name] = student.first_name + " " + student.last_name
    return names

def missingEvalers(currentWeek, evals, students):
    missingNames = []
    for student in students:
        if not evals[currentWeek-1].get(student.user_name) and student.is_active:
           missingNames.append(student.user_name)
    return missingNames
def computeWeightedRanks(currentWeek, connection, reversedEvals, weightsForAverageRank):
    weightedRank = {}
    for evalee in reversedEvals[currentWeek-1]:
        weightedRank[evalee] = 0
        weightsSum = 0
        for evaler in reversedEvals[currentWeek-1][evalee]:
            rank = reversedEvals[currentWeek-1][evalee][evaler][1]
            weeks = connection[evalee][evaler]
            for week in weeks:                
                weightedRank[evalee] += rank * weightsForAverageRank[week-1]
                weightsSum += weightsForAverageRank[week-1]
        weightedRank[evalee] = round(weightedRank[evalee] / weightsSum, round_digits)
    return weightedRank

def mostFrequentAdjectives(currentWeek, reversedEvals):
    result = {}
    for evalee in reversedEvals[currentWeek-1]:
        dict = {}
        for evaler in reversedEvals[currentWeek-1][evalee]:
            adjs = reversedEvals[currentWeek-1][evalee][evaler][0].adjective.split(' ,.')
            for adj in adjs:
                count = dict.get(adj)
                if not count:
                    count = 0
                dict[adj] = count + 1
        result[evalee] = max(dict.iteritems(), key=operator.itemgetter(1))[0]
    return result
             
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    global session
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        engine = create_engine('mysql://' + username + ':' + pwd + '@' + host +':' + port + '/' + schema)
        try:
            engine.connect()
            Base.metadata.bind = engine
            DBSession = sessionmaker(bind=engine)
            session = DBSession()
        
            return redirect(url_for('main'))
        except:
            error = 'Invalid Credentials. Please try again.'
            return render_template('admin_login.html', error=error)
    return render_template('admin_login.html')
    
@app.route('/set_alias/<int:semester_id>', methods=['GET', 'POST'])
def set_alias(semester_id):
    students = queryStudents(semester_id)
    if request.method == 'POST':
        student_id = request.form['student']
        alias = request.form['alias_name']
        student = session.query(Student).filter_by(user_name=student_id).one()
        student.alias_name = alias
        session.commit()
    return render_template('alias.html', students=students)
    
@app.route('/drop_class/<int:semester_id>', methods=['GET', 'POST'])
def drop_class(semester_id):
    students = queryStudents(semester_id)
    if request.method == 'POST':
        student_id = request.form['student']
        student = session.query(Student).filter_by(user_name=student_id).one()
        if request.form['submit'] == 'Add':
            student.is_active = 1
        elif request.form['submit'] == 'Drop':
            student.is_active = 0
        session.commit()
    return render_template('drop.html', students=students)   
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
        