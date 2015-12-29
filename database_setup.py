import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, VARCHAR, TIMESTAMP, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from ConfigParser import SafeConfigParser
from flask.ext.wtf import Form
from wtforms import IntegerField, TextField, validators, FieldList, FormField, TextAreaField, HiddenField, RadioField, SelectField
from wtforms.validators import Required, Length, Optional
from wtforms import Form as WTForm

Base = declarative_base()

class Student(Base):
    __tablename__ = 'student'
    user_name = Column(VARCHAR(15), primary_key=True)
    first_name = Column(VARCHAR(50), nullable=False)
    last_name = Column(VARCHAR(50), nullable=False)
    email = Column(VARCHAR(50))
    login_key = Column(VARCHAR(50))
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    alias_name = Column(VARCHAR(11))
    is_active = Column(Integer, server_default='1')
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'user_name': self.user_name,
            'email': self.email,
            'alias_name': self.alias_name,
			'login_key': self.login_key
        }
        
class Semester(Base):  
    __tablename__ = 'semester'
    __table_args__ = (
            UniqueConstraint('year', 'season', 'course_no'),
            )
    year = Column(Integer, nullable=False)
    season = Column(VARCHAR(11), nullable=False)
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_no = Column(VARCHAR(11), nullable=False)
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'year': self.year,
            'season': self.season,
            'id': self.id,
            'course_no': self.course_no,
        }

class Manager_Eval(Base):
    __tablename__ = 'manager_eval'
    manager_id = Column(Integer, primary_key=True, autoincrement=True)
    approachable_attitude = Column(Integer, nullable=False)
    team_communication = Column(Integer, nullable=False)
    client_interaction = Column(Integer, nullable=False)
    decision_making = Column(Integer, nullable=False)
    resource_utilization = Column(Integer, nullable=False)
    follow_up_to_completion = Column(Integer, nullable=False)
    task_delegation_and_ownership = Column(Integer, nullable=False)
    encourage_team_development = Column(Integer, nullable=False)
    realistic_expectation = Column(Integer, nullable=False)
    performance_under_stress = Column(Integer, nullable=False)
    mgr_description = Column(String(4096), nullable=False)
    
    def parse(self, encryptedManagerEval):
        self.approachable_attitude = encryptedManagerEval.approachable_attitude
        self.team_communication = encryptedManagerEval.team_communication
        self.client_interaction = encryptedManagerEval.client_interaction
        self.decision_making = encryptedManagerEval.decision_making
        self.resource_utilization = encryptedManagerEval.resource_utilization
        self.follow_up_to_completion = encryptedManagerEval.follow_up_to_completion
        self.task_delegation_and_ownership = encryptedManagerEval.task_delegation_and_ownership
        self.encourage_team_development = encryptedManagerEval.encourage_team_development
        self.realistic_expectation = encryptedManagerEval.realistic_expectation
        self.performance_under_stress = encryptedManagerEval.performance_under_stress
        self.mgr_description = encryptedManagerEval.mgr_description
        
class EncryptedManagerEval(Base):
    __tablename__ = 'encrypted_manager_eval'
    manager_id = Column(Integer, primary_key=True, autoincrement=True)
    approachable_attitude = Column(String(128), nullable=False)
    team_communication = Column(String(128), nullable=False)
    client_interaction = Column(String(128), nullable=False)
    decision_making = Column(String(128), nullable=False)
    resource_utilization = Column(String(128), nullable=False)
    follow_up_to_completion = Column(String(128), nullable=False)
    task_delegation_and_ownership = Column(String(128), nullable=False)
    encourage_team_development = Column(String(128), nullable=False)
    realistic_expectation = Column(String(128), nullable=False)
    performance_under_stress = Column(String(128), nullable=False)
    mgr_description = Column(String(4096), nullable=False)
    
    def parse(self, rawManagerEval):
        self.approachable_attitude = rawManagerEval.approachable_attitude
        self.team_communication = rawManagerEval.team_communication
        self.client_interaction = rawManagerEval.client_interaction
        self.decision_making = rawManagerEval.decision_making
        self.resource_utilization = rawManagerEval.resource_utilization
        self.follow_up_to_completion = rawManagerEval.follow_up_to_completion
        self.task_delegation_and_ownership = rawManagerEval.task_delegation_and_ownership
        self.encourage_team_development = rawManagerEval.encourage_team_development
        self.realistic_expectation = rawManagerEval.realistic_expectation
        self.performance_under_stress = rawManagerEval.performance_under_stress
        self.mgr_description = rawManagerEval.mgr_description
        
class Evaluation(Base):
    __tablename__ = 'evaluation'

    evaler_id = Column(VARCHAR(10), ForeignKey(Student.user_name, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    evalee_id = Column(VARCHAR(10), ForeignKey(Student.user_name, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    week = Column(Integer, primary_key=True, autoincrement=False)
    rank = Column(Integer, nullable=False)
    token = Column(Integer, nullable=False)
    description = Column(String(4096), nullable=False)
    submission_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.current_timestamp())
    adjective = Column(String(128), nullable=False)
    manager_id =  Column(Integer, ForeignKey(EncryptedManagerEval.manager_id, onupdate="CASCADE", ondelete="CASCADE"))
    semester_id = Column(Integer, ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    evaler = relationship(Student, foreign_keys='Evaluation.evaler_id')
    evalee = relationship(Student, foreign_keys='Evaluation.evalee_id')
    semester = relationship(Semester)
    encryptedManagerEval = relationship(EncryptedManagerEval)
    
    def parse(self, encryptedEval):
        self.evaler_id = encryptedEval.evaler_id
        self.evalee_id = encryptedEval.evalee_id
        self.week = encryptedEval.week
        #self.rank = encryptedEval.rank
        #self.token = encryptedEval.token
        #self.description = encryptedEval.description
        self.submission_time = encryptedEval.submission_time
        #self.adjective = encryptedEval.adjective
        self.manager_id = encryptedEval.manager_id
        self.semester_id = encryptedEval.semester_id
        self.evaler = encryptedEval.evaler
        self.evalee = encryptedEval.evalee
        self.semester = encryptedEval.semester
        self.encryptedManagerEval = encryptedEval.encryptedManagerEval
        
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'evaler_id': self.evaler_id,
            'evalee_id': self.evalee_id,
            'week': self.week,
            'rank': self.rank,
            'token': self.token,
            'description': self.description,
            'adjective': self.adjective,
        }
        
class EncryptedEvaluation(Base):
    __tablename__ = 'encrypted_evaluation'

    evaler_id = Column(VARCHAR(10), ForeignKey(Student.user_name, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    evalee_id = Column(VARCHAR(10), ForeignKey(Student.user_name, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    week = Column(Integer, primary_key=True, autoincrement=False)
    rank = Column(String(128), nullable=False)
    token = Column(String(128), nullable=False)
    description = Column(String(4096), nullable=False)
    submission_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.current_timestamp())
    adjective = Column(String(128), nullable=False)
    manager_id =  Column(Integer, ForeignKey(EncryptedManagerEval.manager_id, onupdate="CASCADE", ondelete="CASCADE"))
    semester_id = Column(Integer, ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    evaler = relationship(Student, foreign_keys='EncryptedEvaluation.evaler_id')
    evalee = relationship(Student, foreign_keys='EncryptedEvaluation.evalee_id')
    semester = relationship(Semester)
    encryptedManagerEval = relationship(EncryptedManagerEval)
    
    def parse(self, rawEval):
        self.evaler_id = rawEval.evaler_id
        self.evalee_id = rawEval.evalee_id
        self.week = rawEval.week
        #self.rank = rawEval.rank
        #self.token = rawEval.token
        #self.description = rawEval.description
        self.submission_time = rawEval.submission_time
        #self.adjective = rawEval.adjective
        self.manager_id = rawEval.manager_id
        self.semester_id = rawEval.semester_id
        self.evaler = rawEval.evaler
        self.evalee = rawEval.evalee
        self.semester = rawEval.semester
        self.encryptedManagerEval = rawEval.encryptedManagerEval
        
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'evaler_id': self.evaler_id,
            'evalee_id': self.evalee_id,
            'week': self.week,
            'rank': self.rank,
            'token': self.token,
            'description': self.description,
            'adjective': self.adjective,
        }
        
    
class Enrollment(Base):
    __tablename__ = 'enrollment'
    student_id = Column(VARCHAR(10), ForeignKey('student.user_name', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    semester_id = Column(Integer, ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    student = relationship(Student)
    semester = relationship(Semester)
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'student_id': self.student_id,
            'semester_id': self.semester_id,
        }

class Groups(Base):
    __tablename__ = 'groups'
    semester_id = Column(Integer, ForeignKey('semester.id', onupdate="CASCADE", ondelete="CASCADE"))
    week = Column(Integer, nullable=False)
    id = Column(Integer, primary_key=True, autoincrement=True)
    name =  Column(VARCHAR(50))
    assignment_name = Column(VARCHAR(50))
    semester = relationship(Semester)
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
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
    group_id = Column(Integer, ForeignKey('groups.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    student_id = Column(VARCHAR(10), ForeignKey('student.user_name', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    is_manager = Column(Integer, nullable=False, server_default='0')
    student = relationship(Student)
    groups = relationship(Groups)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'student_id': self.student_id,
            'group_id': self.group_id,
        }

class ManagerEvalForm(WTForm):
    choices = [('1','1'),('2','2'),('3','3'),('4','4'),('5','5')]
    approachable = RadioField('Approachable', choices=choices, validators=[Optional()])
    communication = RadioField('Communication', choices=choices, validators=[Optional()])
    client_interaction = RadioField('Client Interaction', choices=choices, validators=[Optional()])
    decision_making = RadioField('Decision Making', choices=choices, validators=[Optional()])
    resource_utilization = RadioField('Resource Utilization', choices=choices, validators=[Optional()])
    follow_up_to_completion = RadioField('Follow up to completion', choices=choices, validators=[Optional()])
    task_delegation_and_ownership = RadioField(u'Task Delegation & Ownership', choices=choices, validators=[Optional()])
    encourage_team_development = RadioField('Encourage Team Development', choices=choices, validators=[Optional()])
    realistic_expectation = RadioField('Realistic Expectation', choices=choices, validators=[Optional()])
    performance_under_stress = RadioField('Performance Under Stress', choices=choices, validators=[Optional()])
    
class EvalForm(WTForm):
    evaler_id = HiddenField('evaler_id', validators=[Required()])
    evalee_id = HiddenField('evalee_id', validators=[Required()])
    week = HiddenField('week', validators=[Required()])
    rank = IntegerField('Rank', validators=[Required()])
    tokens = IntegerField(u'Tokens', validators=[Required()])
    adjective = TextField('Adjective', validators=[Required()])
    description = TextAreaField('Description', validators=[Required()])
    is_manager = IntegerField('is_manager', validators=[Optional()])
    managerEval = FormField(ManagerEvalForm)
    
        
class EvalListForm(Form):
    evaluations = FieldList(FormField(EvalForm))

if __name__ == '__main__':    
    parser = SafeConfigParser()
    parser.read('config.ini')
    username = parser.get('login', 'username')
    password = parser.get('login', 'password')
    schema = parser.get('login', 'schema')
    host = parser.get('login', 'host')
    port = parser.get('login', 'port')


    engine = create_engine('mysql://' + username + ':' + password + '@' + host +':' + port + '/' + schema) 

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Base.metadata.tables["evaluation"].drop(bind = engine)
