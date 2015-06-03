#!/usr/bin/python

import os
import tornado.web
import tornado.iostream
import MySQLdb
import json
import hashlib
import uuid
import time

import TaxPy.inputFile_management.load_file as TaxLoad
import TaxPy.inputFile_management.align_file_manager as TaxFileManager
import TaxPy.db_management.db_wrap as TaxDb


from multiprocessing.pool import ThreadPool
from contextlib import closing

_workers=ThreadPool(5)

class TaxAssessor(tornado.web.Application):
    """
    Class to set up the webserver via passing arguments to web.Application
    in addition to creating the MySQL database.
    """
    def __init__(self, *args, **kwargs):
        print "Starting webserver"
        self.dbName = "TaxAssessor_Users"
        self.connectToDatabase()
        tornado.web.Application.__init__(self, *args, **kwargs)

    def connectToDatabase(self):
        """
        Connects to MySQL database.  If database does not exist, create the
        database by reading in sql setup file "db_setup.sql".
        """
        try:
            self.db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",
                    db=self.dbName)
            self.db.close()
        except MySQLdb.OperationalError:
            self.db = MySQLdb.connect(user="taxassessor",passwd="taxassessor")
            with open("db_setup.sql","r") as sqlFile, closing(self.db.cursor()) as cur:
                cur.execute(sqlFile.read())
            self.db.close()   

class BaseHandler(tornado.web.RequestHandler):
    """
    Parent class containing helper functions for all handlers.
    """
    def get_current_user(self):
        return self.get_secure_cookie("TaxUser")

    def get_current_firstName(self):
        """
        Attempts to retrieve first name of user from the issued cookie.  If no
        cookie exists, None is returned.
        """
        try:
            user = self.get_secure_cookie("TaxUser")
            user = json.loads(user)
            return user['firstName']
        except Exception:
            return None

    def get_current_username(self):
        """
        Attempts to retrieve username (email) of current user via the issued
        cookie.  If no cookie exists, None is returned.
        """
        try:
            user = self.get_secure_cookie("TaxUser")
            user = json.loads(user)
            return user['username']
        except Exception:
            return None

    def get_current_fileListing(self,userName):
        """
        Attempts to retrieve file listing from cookie.  If no cookie exists,
        return None.
        """          
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = "SELECT filename FROM files WHERE username=%s;"
            cur.execute(cmd,userName)
            fileInfo = [item[0] for item in cur.fetchall()]
            return fileInfo

    @tornado.web.authenticated
    def get_current_fileName(self,userName):
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = "SELECT currentFile FROM users WHERE username=%s;"
            cur.execute(cmd,userName)
            fileName = cur.fetchone()[0]
            return fileName


class Index(BaseHandler):
    """
    Handler to render the home page of TaxAssessor.
    """
    def get(self):
        firstName = self.get_current_firstName()
        if firstName is not None:
            userName = self.get_current_username()
            fileListing = self.get_current_fileListing(userName)
            openFile = self.get_current_fileName(userName)
        else:
            fileListing = []
            openFile = None
            userName = None
        self.render("index.html",user=firstName,fileListing=fileListing,
                    openFile=openFile,username=userName)

class Login(BaseHandler):
    """
    Handler for login operations.
    """
    def get(self):
        self.render("login.html",error="")

    def post(self):
        """
        When a login attempt has been posted, retrieve the information and
        execute loginUser to check the information against the database.
        """
        username = self.get_argument("emailAddress","")
        password = self.get_argument("password","")
        loginInfo = {"username":   username,
                     "password":   password}
        self.loginUser(loginInfo)

    def loginUser(self,loginInfo):
        """
        Secure login function.  Given a dictionary containing each a username
        and password key pair, generate the h(salt+trial_password) to check 
        against the h(salt+stored_password) in the MySQL database.
        If login successful, issue a cookie containing username and firstName.
        If login unsuccessful, render the login.html page with an error message.
        """
        #retrieve salt to generate salt-hashed password
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = ('SELECT salt FROM users WHERE username=%s;')
            params = (loginInfo['username'])
            cur.execute(cmd,params)
            try:
                salt = cur.fetchone()[0]
                loginInfo['password'] = (hashlib.sha512(loginInfo['password']+
                                         salt).hexdigest())
            except TypeError:
                self.render("login.html",error="Invalid username or password")
                return

            #check salt-hashed password
            cmd = ('SELECT username,firstName from users where username=%s and '
                   'password=%s;')
            params = (loginInfo['username'],loginInfo['password'])
            cur.execute(cmd,params)
            row = cur.fetchone()
            if row is not None:
                loginInfo = { 'username':   row[0],
                              'firstName':  row[1]}
                loginInfo = json.dumps(loginInfo)
                self.set_secure_cookie("TaxUser",loginInfo,expires_days=5)
                #self.set_fileListing_cookie(row[0])
                self.redirect(r"/")
            else:
                self.render("login.html",error="Invalid username or password")

class Register(Login):
    """
    Handler to process registration requests.
    """
    def get(self):
        self.render("register.html",error="")

    def post(self):
        """
        When a registration request has been posted, retrieve the information,
        pass them through a value checking function, and if the values pass, 
        issue database command to create the user.  If the values do not pass,
        render the registration page with an error message.
        """
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
            with TaxDb.openDb("TaxAssessor_Users") as db, \
                                  TaxDb.cursor(db) as cur:
                cmd = ('INSERT INTO users (username,password,firstName,lastName'
                       ',salt) VALUES (%s,%s,%s,%s,%s);')
                params = (username,hashed_password,firstName,lastName,salt)
                cur.execute(cmd,params)
                db.commit() 
            loginInfo = {'username': username,
                         'password': password}
            self.loginUser(loginInfo)

    def checkValues(self,username,password,firstName,lastName):
        """
        Function to check registration values against a blacklist (most likely
        unnecessary), make sure they are not blank (can be done in javascript
        to avoid a server query), and makes sure that the current email address
        is not already being used.  Returns "True" if values pass, otherwise
        returns false.
        """
        blackList = ["'",'"',"{","}","(",")","/","'\'","[","]"]
        for entry in [username,password,firstName,lastName]:
            if len(entry) == 0:
                errorMessage = "Please fill in all fields"
                return errorMessage,False
            for char in blackList:
                if char in entry:
                    errorMessage = "Invalid character detected"
                    return errorMessage,False
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = "SELECT username FROM users WHERE username=%s;"
            cur.execute(cmd,username)
            row = cur.fetchone()
            if row is not None:
                errorMessage = "Email address already registered"
                return errorMessage,False

        return "",True

class Logout(BaseHandler):
    """
    Logout handler.  Revokes all cookies and redirects to home page.
    """
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("TaxUser")
        self.clear_cookie("TaxFiles")
        self.redirect("/")

def run_background(func, callback, args=(), kwds={}):
    def _callback(result):
        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(result))
    _workers.apply_async(func, args, kwds, _callback)
 
class Upload(BaseHandler):
    """
    Handler to perform upload operations.
    """
    @tornado.web.asynchronous
    @tornado.web.authenticated
    def post(self):
        """
        When an upload request has been posted, spawn a new thread to handle 
        the upload.
        """
        self.start = time.time()
        try:
            fileInfo = self.request.files['upFile'][0]
            userName = self.get_current_username()
            run_background(TaxFileManager.blocking_task, self.on_complete, (fileInfo,userName))
        except Exception:
            self.write("Error receiving file")
            raise StopIteration
    
    def on_complete(self, res):
        self.write(res)
        self.finish()
        self.end = time.time()
        print (self.end-self.start),"seconds for all file processing"
        if "Error" in res:
            raise StopIteration
        
class Open(BaseHandler):
    def get(self):
        pass

    @tornado.web.authenticated
    def post(self):
        fileName = self.get_argument("fileName")
        userName = self.get_current_username()
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = "UPDATE users SET currentFile=%s WHERE username=%s;"
            cur.execute(cmd,(fileName,userName))
            db.commit()
        self.redirect("/")

class Close(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        fileName = None
        userName = self.get_current_username()
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = "UPDATE users SET currentFile=%s WHERE username=%s;"
            cur.execute(cmd,(fileName,userName))
            db.commit()
        self.redirect("/")

class Delete(BaseHandler):
    """
    Handles delete requests.
    """
    def get(self):
        pass
 
    @tornado.web.authenticated
    def post(self):
        """
        When a delete request is posted, the file in question is removed from
        the hard disk as well as the corresponding database entry.
        """
        fileName = self.get_argument("fileName")
        userName = self.get_current_username()
        
        alignFile = TaxFileManager.AlignFile(userName,fileName=fileName)
        alignFile.deleteRecords()

        openFile = self.get_current_fileName(userName)

        print openFile,fileName

        if fileName == openFile:
            with TaxDb.openDb("TaxAssessor_Users") as db, \
                                  TaxDb.cursor(db) as cur:
                cmd = "UPDATE users SET currentFile=%s WHERE username=%s;"
                cur.execute(cmd,(None,userName))
                db.commit()

class ServeFile(tornado.web.StaticFileHandler):
    def get(self,path):
        super(ServeFile,self).get(path)
    
    def get_current_user(self):
        try: 
            user = self.get_secure_cookie("TaxUser")
            user = json.loads(user)
            userid = user['firstName'] 
            return True
        except Exception:
            return False

    def get_current_username(self):
        try:
            user = self.get_secure_cookie("TaxUser")
            user = json.loads(user)
            userName = user['username']
            return True
        except Exception:
            return None






