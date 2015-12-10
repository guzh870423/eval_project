import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, VARCHAR, TIMESTAMP, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from ConfigParser import SafeConfigParser
from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation, EvalForm, EvalListForm

course_no = 'P532'
engine = create_engine('mysql://root:pass123@localhost:3306/eval') 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

Base0 = declarative_base()
engine0 = create_engine('mysql://root:pass123@localhost:3306/eval0')  
Base0.metadata.bind = engine0
DBSession0 = sessionmaker(bind=engine0)
session0 = DBSession0()

class Semester0(Base0):  
    __tablename__ = 'SEMESTER'
    __table_args__ = (
            UniqueConstraint('YEAR', 'SEASON'),
            )
    YEAR = Column(Integer, nullable=False)
    SEASON = Column(VARCHAR(11), nullable=False)
    CREATE_TIME = Column(TIMESTAMP, nullable=False, server_default=func.now())
    ID = Column(Integer, primary_key=True, autoincrement=True)
    def convert(self):
        semester = Semester()
        semester.id = self.ID
        semester.year = self.YEAR
        semester.season = self.SEASON
        semester.create_time = self.CREATE_TIME
        semester.course_no = course_no
        return semester
        
class Student0(Base0):
    __tablename__ = 'STUDENT'
    USER_NAME = Column(VARCHAR(10), primary_key=True)
    FIRST_NAME = Column(VARCHAR(50), nullable=False)
    LAST_NAME = Column(VARCHAR(50), nullable=False)
    EMAIL = Column(VARCHAR(50))
    CREATE_TIME = Column(TIMESTAMP, nullable=False, server_default=func.now())
    SEMESTER_ID = Column(Integer, ForeignKey('SEMESTER.ID', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    IU_USER_NAME = Column(VARCHAR(10), nullable=False)
    SEMESTER = relationship(Semester0)

    def convert(self):
        student = Student()
        student.user_name = self.USER_NAME
        student.first_name = self.FIRST_NAME
        student.last_name = self.LAST_NAME
        student.email = self.EMAIL
        semester = session0.query(Semester0).filter_by(id=self.SEMESTER_ID).first()
        enrollment = Enrollment(student=student, semester=semester)
        return student, enrollment
    
class Evaluation0(Base0):
    __tablename__ = 'EVALUATION'

    EVALER_ID = Column(VARCHAR(10), ForeignKey(Student0.USER_NAME, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    EVALEE_ID = Column(VARCHAR(10), ForeignKey(Student0.USER_NAME, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    WEEK = Column(Integer, primary_key=True, autoincrement=False)
    RANK = Column(Integer, nullable=False)
    TOKEN = Column(Integer, nullable=False)
    DESCRIPTION = Column(String(4096), nullable=False)
    SUBMISSION_TIME = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.current_timestamp())
    ADJECTIVE = Column(String(128), nullable=False)
    semester_id = Column(Integer, ForeignKey('SEMESTER.ID', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    evaler = relationship(Student0, foreign_keys='Evaluation0.EVALER_ID')
    evalee = relationship(Student0, foreign_keys='Evaluation0.EVALEE_ID')
    SEMESTER = relationship(Semester0)

        

class Groups0(Base0):
    __tablename__ = 'GROUPS'
    SEMESTER_ID = Column(Integer, ForeignKey('SEMESTER.ID', onupdate="CASCADE", ondelete="CASCADE"))
    WEEK = Column(Integer, nullable=False)
    ID = Column(Integer, primary_key=True, autoincrement=True)
    name =  Column(VARCHAR(50))
    assignment_name = Column(VARCHAR(50))
    SEMESTER = relationship(Semester0)
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())

    
class Group_Student0(Base0):
    __tablename__ = 'GROUP_STUDENT'
    group_id = Column(Integer, ForeignKey('GROUPS.ID', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    student_id = Column(VARCHAR(10), ForeignKey('STUDENT.USER_NAME', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    STUDENT = relationship(Student0)
    GROUPS = relationship(Groups0)

if __name__ == '__main__':
    semesters0 = session0.query(Semester0).all();
    for semester0 in semesters0:
        semester = semester0.convert()
        session.add(semester)
        
    session.commit()
