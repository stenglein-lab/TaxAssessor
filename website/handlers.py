#!/usr/bin/python

import os
import tornado.web
import tornado.iostream
import MySQLdb
import json
import hashlib
import uuid
import time
import multiprocessing
import datetime
import copy

import TaxPy.inputFile_management.load_file as TaxLoad
import TaxPy.inputFile_management.align_file_manager as TaxFileManager
import TaxPy.db_management.db_wrap as TaxDb
import TaxPy.data_processing.inspect_reads as TaxReads
import TaxPy.data_processing.compare_trees as TaxCompare

from tornado.escape import json_encode

#from multiprocessing.pool import ThreadPool
#from contextlib import closing
#from ctypes import c_char_p

#_workers=ThreadPool(5)

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
            with open("db_setup.sql","r") as sqlFile, \
                    closing(self.db.cursor()) as cur:
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
            cmd = "SELECT filename,dateModified,status FROM files WHERE username=%s;"
            cur.execute(cmd,userName)
            fileInfo = []
            dates = []
            statuses = []
            f = '%Y-%m-%d %H:%M:%S'
            for item in cur.fetchall():
                fileInfo.append(item[0])
                dates.append(item[1].strftime(f))
                statuses.append(item[2])
            return fileInfo,dates,statuses

    @tornado.web.authenticated
    def get_current_fileName(self):
        fileName = self.get_secure_cookie("TaxOpenFiles")
        return fileName

    @tornado.web.authenticated
    def get_current_fileName_tableName(self,userName,fileName):
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = """SELECT uniqueId FROM files WHERE username=%s and
                                                         filename=%s;"""
            cur.execute(cmd,(userName,fileName))
            fileId = cur.fetchone()[0]
            return fileId
    
    @tornado.web.authenticated
    def get_current_set_list(self,userName):
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            fileSets = set()
            cmd = "SELECT setName FROM fileSets WHERE userName=%s;"
            cur.execute(cmd,userName)
            for setName in cur.fetchall():
                fileSets.add(setName[0])
        return sorted(list(fileSets))
        
class Index(BaseHandler):
    """
    Handler to render the home page of TaxAssessor.
    """
    def get(self):
        firstName = self.get_current_firstName()
        if firstName is not None:
            userName = self.get_current_username()
            fileListing,dates,statuses = self.get_current_fileListing(userName)
            openFile = self.get_current_fileName()
            setNames = self.get_current_set_list(userName)
        else:
            fileListing = []
            openFile = None
            userName = None
            setNames = None
            dates    = None
            statuses = None
        self.render("index.html",user=firstName,fileListing=fileListing,
                    openFile=openFile,userName=userName,setNames=setNames,
                    dateModified=dates,statuses=statuses)

class Login(BaseHandler):
    """
    Handler for login operations.
    """
    def get(self):
        self.render("login.html",user=None,error="")

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
                self.render("login.html",error="Invalid username or password",
                            user=None)
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
                self.set_secure_cookie("TaxUser",loginInfo,expires_days=10)
                #self.set_fileListing_cookie(row[0])
                self.redirect(r"/")
            else:
                self.render("login.html",error="Invalid username or password",
                            user=None)

class Register(Login):
    """
    Handler to process registration requests.
    """
    def get(self):
        self.render("register.html",user=None,error="")

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
        errorMessage,allow = self.checkValues(username,password,
                                              firstName,lastName)
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
        self.clear_cookie("TaxOpenFiles")
        self.redirect("/")

# def run_background(func, callback, args=(), kwds={}):
    # def _callback(result):
        # tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(result))
    # _workers.apply_async(func, args, kwds, _callback)
 
class Upload(BaseHandler):
    """
    Handler to perform upload operations.
    """
    @tornado.web.authenticated
    def post(self):
        """
        When an upload request has been posted, spawn a new thread to handle 
        the upload.
        """
        start = time.time() 
        status = {}
        loadOptions = self.getLoadOptions()
        return
        
        for file in self.request.files['upFile']:
            try:
                fileName = file['filename']
                print "Filename: "+fileName
                userName = self.get_current_username()
                #run_background(TaxFileManager.blocking_task, self.on_complete, (fileInfo,userName))
                alignFile = TaxFileManager.AlignFile(userName,fileInfo=file)
                status[fileName] = alignFile.importFile(loadOptions)
                print fileName+": "+status[fileName]
                print "=------------------="
            except Exception,e:
                print e
                status[fileName] = "Error receiving file"
        self.write(json_encode(status))   
        end = time.time()
        print (end-start),"seconds for all file processing"
            
    def getLoadOptions(self):
        options = {}
        options["useLca"] = ("True" == self.get_argument('useLca'))
        fileFormat = self.get_argument('fileFormat')
        if fileFormat[0:5] == "Blast":
            options["fileFormat"] = "blast"
            options["delimeter"] = "\t"
            options["giIndex"] = 2
            options["giDelimiter"] = "|"
            options["giSubIndex"] = 2
            options["scoreIndex"] = 11
            options["scorePreference"] = "lower"
            options["header"] = ("QueryID\tSubjectID\t%Ident\tAlignLen\t"
                    "nGapOpen\tqStart\tqEnd\tsubStart\tsubEnd\teVal\tbitScore")
            
        elif fileFormat[0:3] == "SAM":
            options["fileFormat"] = "sam"
            options["delimeter"] = "\t"
            options["giIndex"] = 3
            options["giDelimiter"] = "|"
            options["giSubIndex"] = 2
            options["scoreIndex"] = 5
            options["scorePreference"] = "higher"
            options["header"] = ("QNAME\tFLAG\tRNAME\tPOS\tMAPQ\tCIGAR\tRNEXT\t"
                                 "PNEXT\tTLEN\tSEQ\tQUAL")
            
        elif fileFormat[0:6] == "Custom":
            options["fileFormat"] = "custom"
            delimiter = self.get_argument("delimiter")
            if delimiter == "Custom":
                options["delimeter"] = str(self.get_argument("customDelimiter"))
            elif delimiter == "Tab":
                options["delimeter"] = "\t"
            elif delimiter == "Space":
                options["delimiter"] = " "
            elif delimiter == "Comma":
                options["delimiter"] = ","
            options["giIndex"] = int(self.get_argument("giIndex"))
            options["giDelimiter"] = str(self.get_argument("giDelimiter"))
            options["giSubIndex"] = int(self.get_argument("giSubIndex"))
            options["scoreIndex"] = int(self.get_argument("scoreIndex"))
            options["scorePreference"] = str(self.get_argument("scorePref"))
            options["header"] = str(self.get_argument("headerData"))
            
        print options
        return options
            
    # def on_complete(self, res):
        # self.write(res)
        # self.finish()
        # self.end = time.time()
        # print (self.end-self.start),"seconds for all file processing"
        # if "Error" in res:
            # raise StopIteration
        
class Open(BaseHandler):
    def get(self):
        pass

    @tornado.web.authenticated
    def post(self):
        fileName = self.get_argument("fileName")
        self.set_secure_cookie("TaxOpenFiles",fileName,expires_days=10)
        self.redirect("/file_report")

class Close(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("TaxOpenFiles")
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

        openFile = self.get_current_fileName()

        print userName,openFile,fileName

class ServeFile(tornado.web.StaticFileHandler):
    @tornado.web.authenticated
    def get(self,path):
        super(ServeFile, self).get(path)
    
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
            
    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")        
        
class InspectReads(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        taxId = self.get_argument("taxId")
        taxName = self.get_argument("taxName")
        
        userName = self.get_current_username()
        fileName = self.get_current_fileName()
        fileId   = self.get_current_fileName_tableName(userName,fileName)
        fileId   = "t"+str(fileId)
        
        readLines,status = TaxReads.retrieveReads(userName,fileName,
                                                  fileId,taxId)

        alignInfo = {"name":taxName,"taxId":taxId,"status":status,
                     "info":readLines}
        self.write(json.dumps(alignInfo))
        
class SaveSet(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        setName = self.get_argument("setName")
        fileNames = self.get_argument("setFiles")
        fileNames = [str(s) for s in fileNames.split()]
        userName = self.get_current_username()
        
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            for fileName in fileNames:
                cmd = ("INSERT INTO fileSets (username, setname, filename) "
                       "VALUES (%s,%s,%s);")
                params = (userName,setName,fileName)
                cur.execute(cmd,params)
            db.commit()
        self.write("Set saved")
        
class GetSetList(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        userName = self.get_current_username()
        setName = self.get_argument("setName")
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = """SELECT filename FROM fileSets WHERE setname=%s and 
                     username=%s"""
            params = (setName,userName)
            cur.execute(cmd,params)
            files = ""
            for fileName in cur.fetchall():
                files += fileName[0] + "\n"
        self.write(files)
             
class ServeReports(BaseHandler):
    @tornado.web.authenticated
    def get(self,path):
        try:
            userName = self.get_current_username()
            currentFile = self.get_current_fileName()
            print currentFile
            print path
            if currentFile:
                self.render(path+".html",
                            userName    = userName,
                            user        = self.get_current_firstName(),
                           fileListing = self.get_current_fileListing(userName),
                            openFile    = currentFile)
            else:
                self.redirect("/")
        except IOError:
            self.write("Page not found")

class CompareSets(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        firstName = self.get_current_firstName()    
        userName = self.get_current_username()
        sets = json.loads(self.get_argument("compareFiles"))
        set1 = sets["set1"]
        set2 = sets["set2"]
        print "Comparing sets: ",set1,set2
        #double check that the files exists
        cmd = "SELECT filename FROM files where filename=%s and username=%s"
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            for treeSet in sets:
                for fileName in sets[treeSet]:
                    cur.execute(cmd,(fileName,userName))
                    if not cur.fetchone():
                        self.write("Error - "+fileName+" DOES NOT EXIST!")
                        return
        
        resultingTree = TaxCompare.compareData(set1,set2,userName)
        with open("uploads/testFile.json","w") as jsonFile:
            jsonFile.write(resultingTree)
        if (len(set1) >= 3) and (len(set2) >= 3):
            pass
        elif (len(set1) >= 3) or (len(set2) >= 3):
            
            self.render("compare_trees.html",userName = userName,user=firstName,
                        compareTrees=resultingTree,fileNames=set1+set2)












