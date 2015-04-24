#!/usr/bin/python

import tornado.web
import MySQLdb
import json

class TaxAssessor(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        print "Starting webserver"
        dbName = "TaxAssessor"
        self.connectToDatabase(dbName)
        tornado.web.Application.__init__(self, *args, **kwargs)

    def connectToDatabase(self,dbName):
        try:
            self.db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",db=dbName)
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

class Index(BaseHandler):
    def get(self):
        firstName = self.get_current_firstName()
        self.render("index.html",user=firstName)

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
        cmd = ('SELECT username,firstName from users where username="{0}" and '
               'password="{1}";'.format(loginInfo['username'],
                                        loginInfo['password']))
        db = self.application.db.cursor()
        db.execute(cmd)
        row = db.fetchone()
        if row is not None:
            loginInfo = { 'username':   row[0],
                          'firstName':  row[1]}
            loginInfo = json.dumps(loginInfo)
            self.set_secure_cookie("TaxUser",loginInfo,expires_days=5)
            self.redirect(r"/")
        else:
            self.render("login.html",error="Invalid username or password")

    def securePassword(self,password):
        pass

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
            cmd = ('INSERT INTO users (username,password,firstName,lastName) '
                   'VALUES ("{0}","{1}","{2}","{3}");'.format(username,password,
                                                             firstName,lastName))
            db = self.application.db.cursor()
            db.execute(cmd)
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
        db = self.application.db.cursor()
        db.execute(cmd)
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




