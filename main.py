from flask import Flask, render_template, url_for, request, redirect
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker
from database_setup import Student, Base, Group, Semester, Group_Student, Enrollment, Evaluation
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('config.ini')
username = parser.get('login', 'username')
password = parser.get('login', 'password')
weightsForAverageRank = []
for weight in parser.get('constants', 'weights_for_average_rank').split(','):
    weightsForAverageRank.append(int(weight))

app = Flask(__name__)

engine = create_engine('mysql://' + username + ':' + password + '@localhost:3306/eval') 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/main')
def main():
    semesters = session.query(Semester).all()
  
    weeks = session.query(distinct(Group.week)).all()
    return render_template('main.html', semesters=semesters, weeks=weeks, str=str)
        
@app.route('/reports/<int:semester_id>/<int:currentWeek>', methods=['GET', 'POST'])
def reports(semester_id, currentWeek):
    semester = session.query(Semester).filter_by(id=semester_id).one()
    print type(currentWeek)
    # list of students' user_name
    students = []
    # Evaluation dictionary: evals[currentWeek][evaler][evalee] = evaluation
    evals = []
    # normalized ranks dictionary: normalizedRanks[Week][evalee][evaler] = normalized_rank
    normalizedRanks = []
    # average rank: averageRank[week][student]
    averageRank = []
    # which weeks do two students work together, connection[student1][student2] = [week1, week2]
    connection = {}
    # weighted rank
    weightedRank = {}
    
    enrollments = session.query(Enrollment).filter_by(semester_id=semester_id).all()
    for enrollment in enrollments:
        student = enrollment.user_name
        students.append(enrollment.user_name)
    
    for previousWeek in range(1, currentWeek+1):
        evalsOneWeek, normalizedRanksOneWeek, averageRankOneWeek = queryEval(semester_id, currentWeek, students)
        evals.append(evalsOneWeek)
        normalizedRanks.append(normalizedRanksOneWeek)
        averageRank.append(averageRankOneWeek)
    #sortedByAverageRank = sorted(averageRank, key=averageRank.get)
    #print sortedByAverageRank

    #intialize connection
    for student1 in students:
        connection[student1] = {}
        for student2 in students:
            connection[student1][student2] = []
    #assign connection
    groups = session.query(Group).all()
    for group in groups:
        studentsInGroup = session.query(Group_Student).filter_by(group_id=group.id).all()
        for student1 in studentsInGroup:
            for student2 in studentsInGroup:
                if student1 != student2:
                    connection[student1.user_name][student2.user_name].append(group.week)
                    
    # compute weighted average rank
    for evalee in normalizedRanks[currentWeek-1]:
        weightedRank[evalee] = 0
        weightsSum = 0
        for evaler, rank in normalizedRanks[currentWeek-1][evalee].iteritems():
            weeks = connection[evalee][evaler]
            for week in weeks:                
                weightedRank[evalee] += rank * weightsForAverageRank[week-1]
                weightsSum += weightsForAverageRank[week-1]
        weightedRank[evalee] /= weightsSum

    return render_template('reports.html',
        semesterName=str(semester.year)+semester.season,
        currentWeek=currentWeek,
        students=students,
        normalizedRanks=normalizedRanks,
        averageRank=averageRank,
        len=len,
        weightedRank=weightedRank,
        )

def queryEval(semester_id, week, students):
    # Evaluation dictionary: evalsOneWeek[evaler][evalee] = evaluation
    evalsOneWeek = {}
    # normalized ranks dictionary: normalizedRanksOneWeek[evalee][evaler] = normalized_rank
    normalizedRanksOneWeek = {}
    # average rank
    averageRankOneWeek = {}
    for evaler in students:
        evalsOneWeek[evaler] = {}
        evalsFromOneStudent = session.query(Evaluation).filter_by(evaler_id=evaler, week=int(week), semester_id=semester_id).all()
        for eval in evalsFromOneStudent:
            evalee = eval.evalee_id
            evalsOneWeek[evaler][evalee] = eval
        
        for evalee, eval in evalsOneWeek[evaler].iteritems():
            if not normalizedRanksOneWeek.get(evalee):
                normalizedRanksOneWeek[evalee] = {}
            normalizedRanksOneWeek[evalee][evaler] = float(eval.rank) / len(evalsOneWeek[evaler])

    for evalee in normalizedRanksOneWeek:
        for evaler, rank in normalizedRanksOneWeek[evalee].iteritems():
            if not averageRankOneWeek.get(evalee):
                averageRankOneWeek[evalee] = 0
            averageRankOneWeek[evalee] += rank / len(normalizedRanksOneWeek[evalee])
    return evalsOneWeek, normalizedRanksOneWeek, averageRankOneWeek
        
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
        