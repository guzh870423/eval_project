#!/usr/bin/env python
# -*- coding:utf-8 -*- 
 
from Crypto.Cipher import AES
from Crypto import Random
from binascii import b2a_hex, a2b_hex
from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation, EncryptedManagerEval
 
class EvalCipher():
    #iv = Random.new().read(AES.block_size)
    iv = u'12345678abcdefgh'
    DUMMY_CHAR = '\0'
    def __init__(self,key):
        self.key = key
        self.mode = AES.MODE_CBC
     
    def encrypt(self,text):
        
        cryptor = AES.new(self.key,self.mode, EvalCipher.iv)
        padded = self.pad(text)
        
        self.ciphertext = cryptor.encrypt(padded)
        #convert encrypted to heximal string
        return b2a_hex(self.ciphertext)
     
    # remove padded char
    def decrypt(self,text):
        cryptor = AES.new(self.key,self.mode, EvalCipher.iv)
        plain_text  = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip(EvalCipher.DUMMY_CHAR)
    
    @staticmethod  
    def pad(text):
        length = 16
        count = len(text)
        add = (length-(count % length))
        return text + (EvalCipher.DUMMY_CHAR * add)
        
    def encryptEval(self, eval):
        encryptedRank = self.encrypt(str(eval.rank))
        encryptedToken = self.encrypt(str(eval.token))
        encryptedadjective = self.encrypt(str(eval.adjective))
        encryptedDescription = self.encrypt(str(eval.description))
        encryptedEval = EncryptedEvaluation()
        encryptedEval.parse(eval)
        encryptedEval.rank = encryptedRank
        encryptedEval.token = encryptedToken
        encryptedEval.adjective = encryptedadjective
        encryptedEval.description = encryptedDescription
        return encryptedEval
        
    def decryptEval(self, encryptedEval):
        rank = self.decrypt(encryptedEval.rank)
        token = self.decrypt(encryptedEval.token)
        adjective = self.decrypt(encryptedEval.adjective)
        description = self.decrypt(encryptedEval.description)
        eval = Evaluation()
        eval.parse(encryptedEval)
        eval.rank = int(rank)
        eval.token = int(token)
        eval.adjective = adjective
        eval.description = description
        return eval
        
    def encryptManagerEval(self, managerEval):
        encryptedApproachableAttitude = self.encrypt(str(managerEval.approachable_attitude))
        encryptedTeamCommunication = self.encrypt(str(managerEval.team_communication))
        encryptedClientInteraction = self.encrypt(str(managerEval.client_interaction))
        encryptedDecisionMaking = self.encrypt(str(managerEval.decision_making))
        encryptedResourceUtilization = self.encrypt(str(managerEval.resource_utilization))
        encryptedFollowUpToCompletion = self.encrypt(str(managerEval.follow_up_to_completion))
        encryptedTaskDelegationAndOwnership = self.encrypt(str(managerEval.task_delegation_and_ownership))
        encryptedEncourageTeamDevelopment = self.encrypt(str(managerEval.encourage_team_development))
        encryptedRealisticExpectation = self.encrypt(str(managerEval.realistic_expectation))
        encryptedPerformanceUnderStress = self.encrypt(str(managerEval.performance_under_stress))
        encryptedDescription = self.encrypt(str(managerEval.mgr_description))
        
        encryptedManagerEval = EncryptedManagerEval()
        encryptedManagerEval.parse(managerEval)
        encryptedManagerEval.approachable_attitude = encryptedApproachableAttitude
        encryptedManagerEval.team_communication = encryptedTeamCommunication
        encryptedManagerEval.client_interaction = encryptedClientInteraction
        encryptedManagerEval.decision_making = encryptedDecisionMaking
        encryptedManagerEval.resource_utilization = encryptedResourceUtilization
        encryptedManagerEval.follow_up_to_completion = encryptedFollowUpToCompletion
        encryptedManagerEval.task_delegation_and_ownership = encryptedTaskDelegationAndOwnership
        encryptedManagerEval.encourage_team_development = encryptedEncourageTeamDevelopment
        encryptedManagerEval.realistic_expectation = encryptedRealisticExpectation
        encryptedManagerEval.performance_under_stress = encryptedPerformanceUnderStress
        encryptedManagerEval.mgr_description = encryptedDescription
        return encryptedManagerEval    
        
# a sample to test EvalCipher 
if __name__ == '__main__':
    pc = EvalCipher('keyskeyskeyskeys') 
    e = pc.encrypt(str(11))
    d = pc.decrypt(e)
    student1 = Student(user_name="adam")
    student2 = Student(user_name="bob")
    semester1 = Semester(year=2015, season="Fall")    
    eval1 = Evaluation(evaler=student1, evalee=student2, week=1, rank=1,token=4, description="i'd love to work", adjective="great", semester=semester1)
    print student1.user_name
    print pc.encryptEval(eval1).evaler_id