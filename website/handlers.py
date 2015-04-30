#!/usr/bin/python

import os
import tornado.web
import tornado.iostream
import MySQLdb
import json
import hashlib
import uuid

from multiprocessing import Process

class TaxAssessor(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        print "Starting webserver"
        self.dbName = "TaxAssessor"
        self.connectToDatabase()
        tornado.web.Application.__init__(self, *args, **kwargs)

    def connectToDatabase(self):
        try:
            self.db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",
                    db=self.dbName)
        except MySQLdb.OperationalError:
            self.db = MySQLdb.connect(user="taxassessor",passwd="taxassessor")
            cur = self.db.cursor()
            with open("db_setup.sql","r") as sqlFile:
                cur.execute(sqlFile.read())

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("TaxUser")

    def get_current_firstName(self):
        try:
            user = self.get_secure_cookie("TaxUser")
            user = json.loads(user)
            return user['firstName']
        except Exception:
            return None

    def get_current_username(self):
        try:
            user = self.get_secure_cookie("TaxUser")
            user = json.loads(user)
            return user['username']
        except Exception:
            return None

    def set_fileListing_cookie(self,username):
        cmd = "SELECT filename FROM files WHERE username=%s;"
        db = self.executeDbCommand(cmd,username)
        fileInfo = [item[0] for item in db.fetchall()]
        fileInfo = json.dumps({"filenames":fileInfo})
        self.set_secure_cookie("TaxFiles",fileInfo,expires_days=5)

    def get_current_fileListing(self):
        try:
            fileNames = self.get_secure_cookie("TaxFiles")
            fileNames = json.loads(fileNames)
            return fileNames["filenames"]
        except Exception:
            return None

    def executeDbCommand(self,cmd,params=None):
        try:
            db = self.application.db.cursor()
            db.execute(cmd,params)
        except (AttributeError, MySQLdb.OperationalError): 
            self.application.db = MySQLdb.connect(user="taxassessor",
                    passwd="taxassessor",db=self.application.dbName)
            db = self.application.db.cursor()
            db.execute(cmd,params)
        return db


class Index(BaseHandler):
    def get(self):
        firstName = self.get_current_firstName()
        fileListing = self.get_current_fileListing()
        self.render("index.html",user=firstName,fileListing=fileListing)


class Login(BaseHandler):
    def get(self):
        self.render("login.html",error="")

    def post(self):
        username = self.get_argument("emailAddress","")
        password = self.get_argument("password","")
        loginInfo = {"username":   username,
                     "password":   password}
        self.loginUser(loginInfo)

    def loginUser(self,loginInfo):
        #retrieve salt to generate salt-hashed password
        cmd = ('SELECT salt FROM users WHERE username=%s;')
        params = (loginInfo['username'])
        db = self.executeDbCommand(cmd,params)
        try:
            salt = db.fetchone()[0]
            loginInfo['password'] = hashlib.sha512(loginInfo['password']+salt).hexdigest()
        except TypeError:
            self.render("login.html",error="Invalid username or password")
            return

        #check salt-hashed password
        cmd = ('SELECT username,firstName from users where username=%s and '
               'password=%s;')
        params = (loginInfo['username'],loginInfo['password'])
        db = self.executeDbCommand(cmd,params)
        row = db.fetchone()
        if row is not None:
            loginInfo = { 'username':   row[0],
                          'firstName':  row[1]}
            loginInfo = json.dumps(loginInfo)
            self.set_secure_cookie("TaxUser",loginInfo,expires_days=5)
            self.set_fileListing_cookie(row[0])
            self.redirect(r"/")
        else:
            self.render("login.html",error="Invalid username or password")


class Register(Login):
    def get(self):
        self.render("register.html",error="")

    def post(self):
        username = self.get_argument("emailAddress","")
        password = self.get_argument("password","")
        firstName = self.get_argument("firstName","")
        lastName = self.get_argument("lastName","")
        errorMessage,allow = self.checkValues(username,password,firstName,lastName)
        if not allow:
            self.render("register.html",error=errorMessage)
        else:
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(password+salt).hexdigest()
            cmd = ('INSERT INTO users (username,password,firstName,lastName,salt) '
                   'VALUES (%s,%s,%s,%s,%s);')
            params = (username,hashed_password,firstName,lastName,salt)
            self.executeDbCommand(cmd,params)
            self.application.db.commit() 
            loginInfo = {'username': username,
                         'password': password}
            self.loginUser(loginInfo)

    def checkValues(self,username,password,firstName,lastName):
        blackList = ["'",'"',"{","}","(",")","/","'\'","[","]"]
        for entry in [username,password,firstName,lastName]:
            if len(entry) == 0:
                errorMessage = "Please fill in all fields"
                return errorMessage,False
            for char in blackList:
                if char in entry:
                    errorMessage = "Invalid character detected"
                    return errorMessage,False
        cmd = "SELECT username FROM users WHERE username='{}'".format(username)
        db = self.executeDbCommand(cmd)
        row = db.fetchone()
        if row is not None:
            errorMessage = "Email address already registered"
            return errorMessage,False

        return "",True

class Logout(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("TaxUser")
        self.redirect("/")

class Upload(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.redirect("/")

    @tornado.web.authenticated
    def post(self):
        uploadProcess = Process(target=self.getFile())
        uploadProcess.start()
        self.redirect("/")

    def getFile(self):
        try:
            fileInfo = self.request.files['upFile'][0]
            print "File Upload: "+str(fileInfo['filename'])
        except Exception:
            self.write("Error receiving file")
            return
        username = self.get_current_username()
        fileName = fileInfo['filename']
        try:
            os.mkdir("uploads/"+username)
        except OSError:
            pass
        with open("uploads/"+username+"/"+fileInfo['filename'],"w") as inFile:
            inFile.write(fileInfo['body'])
        try:
            cmd = "INSERT INTO files (username,filename) VALUES (%s,%s)"
            params = (username,fileName)
            self.executeDbCommand(cmd,params)
            self.application.db.commit()
        except Exception:
            cmd = ("UPDATE files SET dateModified=now() WHERE username=%s and "
                   "filename=%s;")
            params = (username,fileName)
            self.executeDbCommand(cmd,params)
            self.application.db.commit()
        self.set_fileListing_cookie(username)

class Open(BaseHandler):
    def get(self):
        pass

    def post(self):
        fileName = self.get_argument("fileName")
        print fileName
        self.redirect("/")





