#!/usr/bin/python

import os
import multiprocessing
import TaxPy.inputFile_management.load_file as TaxLoad
import TaxPy.db_management.db_wrap as TaxDb
import TaxPy.data_processing.create_tree as TaxTree
from ctypes import c_char_p

# blocking task like querying to MySQL
def blocking_task(fileInfo,userName):
    alignFile = AlignFile(userName,fileInfo=fileInfo)
    status = multiprocessing.Value(c_char_p," -ERROR 1-")
    p = multiprocessing.Process(target=alignFile.importFile,args=[status])
    p.start()
    p.join()
    return status.value

class AlignFile():
    def __init__(self,userName,fileName=None,fileInfo=None):
        self.fileInfo = fileInfo
        if fileInfo == None:
            self.fileName = os.path.splitext(fileName)[0]
        else:
            self.fileName = os.path.splitext(fileInfo['filename'])[0]
        self.userName = userName
    
    def importFile(self,status):
        """
        When an upload has been posted, retrieve the file, attempt to create
        a folder for the user with scheme "uploads/username/" then write the
        file to that directory and create a database record of that file with
        the username.  If the file already exists, touch the row in the database
        to update the timestamp.
        """
        def createDbEntry(self):
            with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
                cmd = "SELECT * FROM files WHERE username=%s AND filename=%s"
                cur.execute(cmd,(self.userName,self.fileName))
                row = cur.fetchone()
                if row != None:
                    raise Exception
                    return
                else:
                    cmd = "INSERT INTO files (username,filename) VALUES (%s,%s);"
                    params = (self.userName.encode("ascii"),self.
                              fileName.encode("ascii"))
                    cur.execute(cmd,params)
                    db.commit()
                    return
        def deleteDbEntry(self):
            with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
                cmd = "DELETE FROM files WHERE username=%s and filename=%s;"
                cur.execute(cmd,(self.userName,self.fileName))
                db.commit() 
                rows = cur.rowcount
        
        try:
            fileBody = self.fileInfo['body']
        except Exception:
            status.value = "Error accessing file"
            return

        try:
            os.mkdir("uploads/"+self.userName)
        except OSError:
            pass
            
        try:
            createDbEntry(self)
        except Exception:
            status.value = "Error: File already exists, please delete first!"
            raise StopIteration
        
        try:
            TaxLoad.loadFile(self.fileName,fileBody,self.userName)
            status.value = "File upload & import successful!"
        except Exception:
            deleteDbEntry(self)
            status.value = "Error: File could not be imported into database"
            raise StopIteration
                
            
    def deleteRecords(self):
        try:
            with TaxDb.openDb("TaxAssessor_Users") as db, \
                                  TaxDb.cursor(db) as cur:
                cmd = ("SELECT uniqueId FROM files WHERE username=%s and "
                       "filename=%s;")
                cur.execute(cmd,(self.userName,self.fileName))
                uniqueId = cur.fetchone()[0]
                cmd = "DELETE FROM files WHERE uniqueId=%s;"
                cur.execute(cmd,(uniqueId))
                db.commit()   
        except Exception:
            pass
        try:
            with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                       TaxDb.cursor(db) as cur:   
                cmd = "DROP TABLE %s;" % ("t"+str(uniqueId))
                cur.execute(cmd)
                db.commit()            
        except Exception:
            pass
        
        try:
            os.remove("uploads/"+self.userName+"/"+self.fileName+".json")
        except Exception:
            pass
            
            
        print "Deleted: "+self.fileName






