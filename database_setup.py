import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, VARCHAR, TIMESTAMP, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('config.ini')
username = parser.get('login', 'username');
password = parser.get('login', 'password');

Base = declarative_base()

class Student(Base):
    __tablename__ = 'student'
    user_name = Column(VARCHAR(10), primary_key=True)
    first_name = Column(VARCHAR(50))
    last_name = Column(VARCHAR(50))
    email = Column(VARCHAR(50))
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'user_name': self.user_name,
            'email': self.email,
        }
        
class Semester(Base):  
    __tablename__ = 'semester'
    __table_args__ = (
            UniqueConstraint('year', 'season'),
            )
    id = Column(Integer(11), primary_key=True, autoincrement=True)
    year = Column(Integer(4), nullable=False)
    season = Column(VARCHAR(11), nullable=False)
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'year': self.year,
            'season': self.season,
        }
        
class Evaluation(Base):
    __tablename__ = 'evaluation'

    evaler_id = Column(VARCHAR(10), ForeignKey(Student.user_name, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    evalee_id = Column(VARCHAR(10), ForeignKey(Student.user_name, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    week = Column(Integer(2), primary_key=True, autoincrement=False)
    rank = Column(Integer(3), nullable=False)
    token = Column(Integer(3), nullable=False)
    description = Column(String(4096), nullable=False)
    submission_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.current_timestamp())
    adj = Column(String(128), nullable=False)
    semester_id = id = Column(Integer(11), ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    #manager_id =  Column(Integer(2), ForeignKey(Manager_Eval.id, , onupdate="CASCADE", ondelete="CASCADE"))
    evaler = relationship(Student, foreign_keys='Evaluation.evaler_id')
    evalee = relationship(Student, foreign_keys='Evaluation.evalee_id')
    semester = relationship(Semester)
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'evaler_id': self.evaler_id,
            #'evalee_id': self.evalee_id,
            'week': self.week,
            'rank': self.rank,
            'token': self.token,
            'description': self.description,
            'adj': self.adj,
            'type': self.type,
        }
        
    
class Enrollment(Base):
    __tablename__ = 'enrollment'
    user_name = Column(VARCHAR(10), ForeignKey('student.user_name', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    semester_id = id = Column(Integer(11), ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    student = relationship(Student)
    semester = relationship(Semester)
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'user_name': self.user_name,
            'semester_id': self.semester_id,
        }

class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer(11), primary_key=True, autoincrement=True)
    week = Column(Integer(2), nullable=False)
    semester_id = Column(Integer(11), ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"))
    name =  Column(VARCHAR(50))
    semester = relationship(Semester)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'week': self.week,
            'semester_id': self.semester_id,
            'name': self.name,
        }
    
class Group_Student(Base):
    __tablename__ = 'group_student'
    group_id = Column(Integer(11), ForeignKey('group.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    user_name = Column(VARCHAR(10), ForeignKey('student.user_name', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    student = relationship(Student)
    group = relationship(Group)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'user_name': self.user_name,
            'group_id': self.group_id,
        }
if __name__ == '__main__':    
    engine = create_engine('mysql://' + username + ':' + password + '@localhost:3306/eval') 

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
