from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Student, Base, Group, Semester, Group_Student, Enrollment, Evaluation
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('config.ini')
username = parser.get('login', 'username');
password = parser.get('login', 'password');

engine = create_engine('mysql://' + username + ':' + password + '@localhost:3306/eval') 
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

#pupulate students
student1 = Student(user_name="adam")
student2 = Student(user_name="bob")
student3 = Student(user_name="charlie")

session.add(student1)
session.add(student2)
session.add(student3)
session.commit()

#semester
semester1 = Semester(year=2015, season="Fall")
session.add(semester1)
session.commit()

#evals
eval1 = Evaluation(evaler=student1, evalee=student2, week=1, rank=1,token=4, description="i'd love to work", adj="great", semester=semester1)
eval2 = Evaluation(evaler=student2, evalee=student1, week=1, rank=1,token=4, description="i'd like to work", adj="good", semester=semester1)
eval3 = Evaluation(evaler=student2, evalee=student1, week=2, rank=1,token=3, description="i'd love to work", adj="great", semester=semester1)
eval4 = Evaluation(evaler=student2, evalee=student3, week=2, rank=2,token=1, description="i'd like to work", adj="good", semester=semester1)
eval5 = Evaluation(evaler=student1, evalee=student2, week=2, rank=1,token=4, description="i'd love to work", adj="great", semester=semester1)
eval6 = Evaluation(evaler=student3, evalee=student2, week=2, rank=1,token=4, description="i'd like to work", adj="good", semester=semester1)
eval7 = Evaluation(evaler=student1, evalee=student2, week=3, rank=1,token=2, description="i'd love to work", adj="great", semester=semester1)
eval8 = Evaluation(evaler=student1, evalee=student3, week=3, rank=2,token=2, description="i'd like to work", adj="good", semester=semester1)
eval9 = Evaluation(evaler=student2, evalee=student1, week=3, rank=1,token=3, description="i'd love to work", adj="great", semester=semester1)
eval10 = Evaluation(evaler=student2, evalee=student3, week=3, rank=2,token=1, description="i'd like to work", adj="good", semester=semester1)
eval11 = Evaluation(evaler=student3, evalee=student1, week=3, rank=1,token=3, description="i'd love to work", adj="great", semester=semester1)
eval12 = Evaluation(evaler=student3, evalee=student2, week=3, rank=2,token=1, description="i'd like to work", adj="good", semester=semester1)
session.add(eval1)
session.add(eval2)
session.add(eval3)
session.add(eval4)
session.add(eval5)
session.add(eval6)
session.add(eval7)
session.add(eval8)
session.add(eval9)
session.add(eval10)
session.add(eval11)
session.add(eval12)
session.commit()


#enrollment
enrollment1 = Enrollment(student=student1, semester=semester1)
enrollment2 = Enrollment(student=student2, semester=semester1)
enrollment3 = Enrollment(student=student3, semester=semester1)
session.add(enrollment1)
session.add(enrollment2)
session.add(enrollment3)
session.commit()

#group
group1 = Group(semester=semester1, week=1)
group2 = Group(semester=semester1, week=2)
group3 = Group(semester=semester1, week=3)
session.add(group1)
session.add(group2)
session.add(group3)
session.commit()

#group_student
group_student1 = Group_Student(group=group1, student=student1)
group_student2 = Group_Student(group=group1, student=student2)
group_student3 = Group_Student(group=group2, student=student2)
group_student4 = Group_Student(group=group2, student=student3)
group_student5 = Group_Student(group=group3, student=student1)
group_student6 = Group_Student(group=group3, student=student3)
session.add(group_student1)
session.add(group_student2)
session.add(group_student3)
session.add(group_student4)
session.add(group_student5)
session.add(group_student6)
session.commit()