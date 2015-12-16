from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation
from ConfigParser import SafeConfigParser
from encrypt import EvalCipher
from sqlalchemy import func, and_
import csv
import openpyxl

parser = SafeConfigParser()
parser.read('config.ini')
username = parser.get('login', 'username')
password = parser.get('login', 'password')
schema = parser.get('login', 'schema')
host = parser.get('login', 'host')
port = parser.get('login', 'port')

engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema) 
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

wb = openpyxl.load_workbook('group-config.xlsx')
wb.get_sheet_names()
sheet = wb.get_sheet_by_name('groups')
print sheet.cell(row=1, column=2).value
rows = sheet.max_row
columns = sheet.max_column
print rows, columns

for row in range(2, rows + 1):
    semester_id = sheet['A' + str(row)].value
    week = sheet['B' + str(row)].value
    group_name = sheet['C' + str(row)].value
    assignment_name = sheet['D' + str(row)].value
    
    semester = session.query(Semester).filter_by(id=semester_id).first()
    group = Groups(semester=semester, week=week, name=group_name, assignment_name=assignment_name)
    session.add(group)

session.commit()

sheet = wb.get_sheet_by_name('group-student')
rows = sheet.max_row
columns = sheet.max_column

for row in range(2, rows + 1):
    group_name = sheet['A' + str(row)].value
    student_id = sheet['B' + str(row)].value
    is_manager = sheet['C' + str(row)].value
    
    max_week = session.query(func.max(Groups.week)).scalar()
    group = session.query(Groups).filter_by(week=max_week, name=group_name).first()
    student = session.query(Student).filter_by(user_name=student_id).first()
    group_student = Group_Student(groups=group, student=student, is_manager = is_manager)
    session.add(group_student)

session.commit()
print "Configuration Data inserted Successfully."
session.close()
