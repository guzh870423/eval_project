#!/usr/bin/env python
# -*- coding:utf-8 -*- 
 
from Crypto.Cipher import AES
from Crypto import Random
from binascii import b2a_hex, a2b_hex
from database_setup import Student, Base, Groups, Semester, Group_Student, Enrollment, Evaluation, EncryptedEvaluation
 
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
        encryptedAdj = self.encrypt(str(eval.adj))
        encryptedDescription = self.encrypt(eval.description)
        encryptedEval = EncryptedEvaluation()
        encryptedEval.parse(eval)
        encryptedEval.rank = encryptedRank
        encryptedEval.token = encryptedToken
        encryptedEval.adj = encryptedAdj
        encryptedEval.description = encryptedDescription
        return encryptedEval
        
    def decryptEval(self, encryptedEval):
        rank = self.decrypt(encryptedEval.rank)
        token = self.decrypt(encryptedEval.token)
        adj = self.decrypt(encryptedEval.adj)
        description = self.decrypt(encryptedEval.description)
        eval = Evaluation()
        eval.parse(encryptedEval)
        eval.rank = int(rank)
        eval.token = int(token)
        eval.adj = adj
        eval.description = description
        return eval
        
# a sample to test EvalCipher 
if __name__ == '__main__':
    pc = EvalCipher('keyskeyskeyskeys') 
    e = pc.encrypt(str(11))
    d = pc.decrypt(e)
    student1 = Student(user_name="adam")
    student2 = Student(user_name="bob")
    semester1 = Semester(year=2015, season="Fall")    
    eval1 = Evaluation(evaler=student1, evalee=student2, week=1, rank=1,token=4, description="i'd love to work", adj="great", semester=semester1)
    print student1.user_name
    print pc.encryptEval(eval1).evaler_id