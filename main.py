from flask import Flask, render_template, url_for, request, redirect
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker
from database_setup import Student, Base, Group, Semester, Group_Student, Enrollment, Evaluation

app = Flask(__name__)

engine = create_engine('mysql://root:sunyinwei@localhost:3306/eval')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/main')
def main():
    semesters = session.query(Semester).all()
  
    weeks = session.query(distinct(Group.week)).all()
    return render_template('main.html', semesters=semesters, weeks=weeks, str=str)
        
@app.route('/reports/<int:semester_id>/<int:week>', methods=['GET', 'POST'])
def reports(semester_id, week):
    semester = session.query(Semester).filter_by(id=semester_id).one()
    
    # list of students' user_name
    students = []
    # Evaluation dictionary: evals[evaler][evalee] = evaluation
    evals = {}
    # normalized ranks dictionary: normalizedRanks[evalee][evaler] = normalized_rank
    normalizedRanks = {}
    # average rank
    averageRank = {}
    
    enrollments = session.query(Enrollment).filter_by(semester_id=semester_id).all()
    for enrollment in enrollments:
        student = enrollment.user_name
        students.append(enrollment.user_name)
        evals[student] = {}
        evalsFromOne = session.query(Evaluation).filter_by(evaler_id=student, week=int(week), semester_id=semester_id).all()
        for eval in evalsFromOne:
            evalee = eval.evalee_id
            evals[student][evalee] = eval
        
        for evalee, eval in evals[student].iteritems():
            if not normalizedRanks.get(evalee):
                normalizedRanks[evalee] = {}
            normalizedRanks[evalee][student] = float(eval.rank) / len(evals[student])
            
    for evalee in normalizedRanks:
        for evaler, rank in normalizedRanks[evalee].iteritems():
            if not averageRank.get(evalee):
                averageRank[evalee] = 0
            averageRank[evalee] += rank / len(normalizedRanks[evalee])
    sortedByAverageRank = sorted(averageRank, key=averageRank.get)
    print sortedByAverageRank
    return render_template('reports.html',
        semesterName=str(semester.year)+semester.season,
        week=week,
        normalizedRanks=normalizedRanks,
        averageRank=averageRank,
        sortedByAverageRank=sortedByAverageRank,
        len=len,
        )
    
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
        