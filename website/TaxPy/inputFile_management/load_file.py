#!/usr/bin/python

import re
import sys
import warnings
import MySQLdb
import TaxPy.db_management.db_wrap as TaxDb
import TaxPy.db_management.permute_db_table as TaxPermute
import TaxPy.data_processing.create_tree_quick as TaxTree
import TaxPy.data_processing.create_read_report as TaxReport
import multiprocessing
import threading
import time

class InputFile():
    def __init__(self,fileName,fileBody,userName):
        self.fileName = fileName
        self.fileBody = fileBody
        self.fileType, self.delimiter = self.detectFileAttributes()
        self.userName = userName
        
    def genLine(self):
        inFile = self.fileBody.splitlines()
        for line in inFile:
            if line:
                yield line

    def detectFileAttributes(self):
        for line in self.genLine():
            firstLine = line
            break
            
        if ";" in firstLine:
            print "invalid character detected in input file"
            raise StopIteration    
            
        delimiters = ["\t"]
        for delimiter in delimiters:
            #testLine = re.split(delimiter,firstLine)
            testLine = firstLine.split(delimiter)
            try: 
                gi = testLine[1].split("|")[1]
                for index in xrange(2,12):
                    value = float(testLine[index])
                print ("Inferred BLAST file type from first line with "
                       "delimiter: "+repr(delimiter))
                return "BLAST",delimiter
            except IndexError:
                pass
            except ValueError:
                pass
  
        print "Could not determine file type of: "+self.fileName
        return None,None

class FileTemplate():
    def __init__(self):
        self.checkForDb()
        self.fileName  = None
        self.fileBody  = None
        self.delimiter = None
        self.userName  = None
        self.dbTableName  = self.getTableName()
        self.readMinScore = {}
            
    def importData(self):
        warnings.warn("NOT YET IMPLEMENTED FOR THIS FILETYPE")

    def checkForDb(self):
        try:
            with TaxDb.openDb("TaxAssessor_Alignments") as db:
                cur = db.cursor()
                cur.close()
        except Exception:
            with TaxDb.dbConnect() as db:
                cur = db.cursor()
                cur.execute("CREATE DATABASE TaxAssessor_Alignments;")
                cur.close()

    def getTableName(self):
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = """SELECT uniqueId from files where 
                     filename=%s and username=%s;"""
            cur.execute(cmd,(self.fileName,self.userName))
            id = int(cur.fetchone()[0])
        return "t"+str(id)
                
class BlastFile(InputFile,FileTemplate):
    def __init__(self,InputFile):
        #Basic File Information
        self.fileName  = InputFile.fileName
        self.fileBody  = InputFile.fileBody
        self.delimiter = InputFile.delimiter
        self.userName  = InputFile.userName
        #Information for building the taxonomy tree
        self.readMinScore = {}
        self.readMinGis = {}
        self.readMinCount = {}
        self.readMinLines = {}
        self.giToTax = None
        #Setting up database table
        self.checkForDb()
        self.dbTableName  = self.getTableName()

    def importData(self):
        """
        A function that reads the uploaded file and extracts the highest 
        alignment(s) for each read.  Once the highest alignments have been
        obtained, two processes are started.  The first preps the data for the
        database import and the second consumes that data and places it into
        the database.
        """
        gis = set()
        taxIds = set()
        taxCount = {}
        giToTax = {}
        giCount = {}
        readMinScore = {}
        readMinGis = {}
        readMinCount = {}
        readMinLines = {}
        
        #move through the file extracting the best alignment(s) for each read.
        for line in self.genLine():
            data = line.split(self.delimiter)
            gi = int(data[1].split("|")[1])
            readName = data[0]
            eValue = data[-2]
            
            if ((readName not in readMinScore) or
                    (eValue < readMinScore[readName])):
                readMinScore[readName] = eValue
                readMinGis[readName] = [gi]
                readMinLines[readName] = [line]
                readMinCount[readName] = 1
            elif eValue == readMinScore[readName]:
                readMinGis[readName].append(gi)
                readMinLines[readName].append(line)
                readMinCount[readName] += 1
    
        #consolidate the GIs and their contributions (normalized count)
        for readName in readMinGis:
            gis = gis.union(readMinGis[readName])
            contribution = 1.0/readMinCount[readName]
            for gi in readMinGis[readName]:
                if gi in giCount:
                    giCount[gi] += contribution
                else:
                    giCount[gi] = contribution
        
        #get the TaxIDs from the list of GIs.
        gistring = "("+str(gis).lstrip("set([").rstrip("])")+")"
        cmd = "SELECT gi,taxID from GiTax_NCBI WHERE gi in "+gistring
        with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                               TaxDb.cursor(db) as cur:
            cur.execute(cmd)
            for data in cur:
                gi = int(data[0])
                taxId = int(data[1])
                if taxId == 0:
                    taxId = -1
                giToTax[gi] = taxId
        
        #begin processes that prepare the data and perform the database import
        parent,child = multiprocessing.Pipe()
        p=[]
        p.append(multiprocessing.Process(target=self.consumeDumpIntoDb,
                                         args=(child,)))
        p.append(multiprocessing.Process(target=self.produceDumpForDb,
                                         args=(readMinGis,readMinLines,
                                               readMinScore,readMinCount,
                                               giToTax,parent)))
        for process in p:
            process.start()
        
        #count up the contributions of GIs that belong to the same TaxID
        for gi in gis:
            if gi in giToTax and giToTax[gi] != 0: # 0 value = unknown
                taxId = giToTax[gi]
            else:
                taxId = -1
            if taxId not in taxIds:
                taxIds.add(taxId)
                taxCount[taxId] = giCount[gi]
            else:
                taxCount[taxId] += giCount[gi]
        
        #begin process to generate read report
        report = TaxReport.ReadReport(readMinGis,readMinScore,
                                      readMinCount,taxCount,gis) 
        readReport = report.createReport()      
                                               
        
        self.giToTax = giToTax
        return taxIds,taxCount,readReport
        
    def createDbTable(self):
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:
            cmd = ("""CREATE TABLE %s (readName     VARCHAR(50) NOT NULL, 
                                       taxId        INT(11) NOT NULL,
                                       count        FLOAT(11) NOT NULL,
                                       eValue       FLOAT(11) NOT NULL,
                                       readLine     VARCHAR(210) NOT NULL,
                                       INDEX (readName),
                                       INDEX (taxId,eValue));"""
                                       % (self.dbTableName))
            cur.execute(cmd)
         
    def produceDumpForDb(self,readMinGis,readMinLines,readMinScore,
                        readMinCount,giToTax,conn):
        countDump = 0
        dump = []
        for readName in readMinGis:
            eValue = readMinScore[readName]
            count = readMinCount[readName]
            for index,gi in enumerate(readMinGis[readName]):
                alignLine = readMinLines[readName][index]
                try:
                    taxId = giToTax[gi]
                except Exception:
                    continue
                countDump += 1
                dump.append((readName,taxId,count,eValue,alignLine))
                if countDump % 10000 == 0:
                    dump = str(dump).rstrip("]").lstrip("[")
                    conn.send(dump)
                    dump = []
        if len(dump) > 0:
            dump = str(dump).rstrip("]").lstrip("[")
            conn.send(dump)
        conn.send(None)
        conn.close()

    def consumeDumpIntoDb(self,conn):
        self.createDbTable()
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:   
            cmd = ("""INSERT INTO %s (readName,taxId,count,eValue,readLine)
                                      VALUES """ % (self.dbTableName))
            cur.execute("START TRANSACTION;")
            cur.execute("SET autocommit=0;")
            dump = []
            while True:
                dump = conn.recv()
                if dump == None:
                    conn.close()
                    return
                else:
                    dump = cmd + dump + ";"
                    cur.execute(dump)
                    db.commit()

def loadFile(fileName,fileBody,userName):
    inputFile = InputFile(fileName,fileBody,userName)
    
    if inputFile.fileType == "BLAST":
        inputFile = BlastFile(inputFile)
        taxIds,taxCount,readReport = inputFile.importData()
        taxTree = TaxTree.createTree(taxIds,taxCount)
        with open("uploads/"+userName+"/"+fileName+"_tree.json","w") as outFile:
            outFile.write(taxTree)
        with open("uploads/"+userName+"/"+fileName+"_readReport.json","w") as outFile:
            outFile.write(readReport)
        return
    else:
        warnings.warn("UNKNOWN FILETYPE! DELETING")
        raise Exception
        return
















