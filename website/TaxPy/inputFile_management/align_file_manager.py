#!/usr/bin/python

import os
import sys
import json
import multiprocessing
import traceback
import TaxPy.inputFile_management.load_file2 as TaxLoad
import TaxPy.db_management.db_wrap as TaxDb
import TaxPy.db_management.importAlignFileIntoDb as TaxDbImport
import TaxPy.data_processing.create_tree as TaxTree
import TaxPy.data_processing.createReports as TaxReports
from ctypes import c_char_p

# blocking task like querying to MySQL
def blocking_task(fileInfo,userName):
    alignFile = AlignFile(userName,fileInfo=fileInfo)
    status = multiprocessing.Value(c_char_p," -ERROR 1-")
    p = multiprocessing.Process(target=alignFile.importFile,args=[status])
    p.start()
    p.join()
    return status.value

class ImportManager():
    def __init__(self,userName,fileName=None,fileInfo=None):
        self.fileInfo = fileInfo
        if fileInfo == None:  #if deleting a file
            self.fileName = fileName
        else:
            self.fileName = fileInfo['filename']
        self.userName = userName
    
    def importFile(self,loadOptions):
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
        def updateDbEntryStatus(self,status):
            with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
                cmd = "UPDATE files SET status=%s WHERE username=%s AND filename=%s"
                cur.execute(cmd,(status,self.userName,self.fileName))
                db.commit()
                
        def handleError(e):
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("ERROR: ",exc_type, fname, exc_tb.tb_lineno)
            traceback.print_exc()
            self.deleteRecords()
            return str(e)

            
        try:
            fileBody = self.fileInfo['body']
        except Exception,e:
            status = "Error accessing file"
            return status

        try:
            os.mkdir("uploads/"+self.userName)
        except OSError:
            pass
            
        try:
            createDbEntry(self)
        except Exception:
            status = "File already exists, please delete first!"
            return status
        
        try:
            updateDbEntryStatus(self,"Processing")
            inputFile = TaxLoad.InputFile(self.fileName,fileBody,self.userName,
                                          loadOptions)  
            (reads,taxa) = inputFile.processData()
            
            #create tree
            tree = TaxTree.Tree(taxa)
            tree = json.dumps(tree.buildTree(1),sort_keys=False)
            this_dir = os.path.dirname(__file__)
            with open(this_dir+"/../../uploads/"+self.userName+"/"+
                    self.fileName+"_tree.json","w") as outFile:
                outFile.write(tree)       
             
            #import data into db
            dbImport = TaxDbImport.DbImport(reads,self.fileName,self.userName)
            dbImport.createDbTable()
            dbImport.importDataIntoDb()   
            
            #create reports
            TaxReports.assessTaxIds(taxa,reads,self.fileName,
                                                     self.userName)
            
            
            
            status = "SUCCESS"
            updateDbEntryStatus(self,"Ready")           
        except Exception as e:
            status = handleError(e)
            
        return status
                
    def deleteRecords(self):
        with TaxDb.openDb("TaxAssessor_Users") as db, \
                              TaxDb.cursor(db) as cur:
            cmd = ("SELECT uniqueId FROM files WHERE username=%s and "
                   "filename=%s;")
            cur.execute(cmd,(self.userName,self.fileName))
            uniqueId = cur.fetchone()[0]
            cmd = "DELETE FROM files WHERE uniqueId=%s;"
            cur.execute(cmd,(uniqueId))
            db.commit()   

        try:
            with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                       TaxDb.cursor(db) as cur:   
                cmd = "DROP TABLE %s;" % ("t"+str(uniqueId))
                cur.execute(cmd)
                db.commit()            
        except Exception:
            print "Error removing file table"
        
        try:
            os.remove("uploads/"+self.userName+"/"+self.fileName+"_tree.json")
            os.remove("uploads/"+self.userName+"/"+self.fileName+"_report.json")
        except Exception:
            print "Error removing flat files"
            
            
        print "Deleted: "+self.fileName






