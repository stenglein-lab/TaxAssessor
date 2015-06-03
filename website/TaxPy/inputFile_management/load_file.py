#!/usr/bin/python

import re
import sys
import warnings
import MySQLdb
import TaxPy.db_management.db_wrap as TaxDb
import TaxPy.db_management.permute_db_table as TaxPermute
import TaxPy.data_processing.create_tree as TaxTree
import multiprocessing
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
        self.uniqueId  = None
    
    def getUniqueId(self):
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = """SELECT uniqueId from files where 
                     filename=%s and username=%s;"""
            cur.execute(cmd,(self.fileName,self.userName))
            id = int(cur.fetchone()[0])
        return id
        
    def createDbTable(self):
        warnings.warn("NOT YET IMPLEMENTED FOR THIS FILETYPE")
        
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

class BlastFile(InputFile,FileTemplate):
    def __init__(self,InputFile):
        self.checkForDb()
        self.fileName  = InputFile.fileName
        self.fileBody  = InputFile.fileBody
        self.delimiter = InputFile.delimiter
        self.userName  = InputFile.userName
        self.uniqueId  = self.getUniqueId()
        self.parent,self.child   = multiprocessing.Pipe()
        self.consumer  = multiprocessing.Process(target = self.loadIntoDb)
        self.consumer.start()
        self.createDbTable()   
        
    def loadIntoDb(self):
        """
        Consumer process with built in error checking
        """
        def mitigateError(dump):
            newdump = []
            for data in dump: #check for known errors & recreate dump
                data = list(data)
                if data[-2] == "inf":  #value inf in evalue, replace with large value
                    data[-2] = 99999
                newdump.append(tuple(data))        
            newdump = str(newdump).rstrip("]").lstrip("[")
            return newdump
        
        warnings.filterwarnings('error', category=MySQLdb.Warning)
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                              TaxDb.cursor(db) as cur:   
            cmd = ("""INSERT INTO %s (taxID,readName,subjectId,percentId,
                                      alignLength,nMismatch,nGapOpens,
                                      qStartPos,qEndPos,tStartPos,tEndPos,
                                      eValue,bitScore,contribution) VALUES """
                                      % ("t"+str(self.uniqueId)))         
            start = time.time()
            while True:
                dump = self.child.recv()
                if dump == None:
                    print "Finished DB import"
                    db.commit()
                    self.child.close()
                    end = time.time()
                    print (end-start)," seconds spent in DB thread"
                    return
                try:
                    values = str(dump).rstrip("]").lstrip("[")
                    cur.execute(cmd+values)
                except Warning:
                    print ("WARNING! ERROR IN BLAST: IF WARNING APPEARS AFTER"
                           " THIS STATEMENT, ERROR IS NOT FIXED PROPERLY!")
                    values = mitigateError(dump)
                    cur.execute(cmd+values)
            
    def processLine(self,line,cur,giToTax):
        data = line.split(self.delimiter)
        gi = int(data[1].split("|")[1])
        if (gi not in giToTax) or (giToTax[gi] == 0):
            taxId = -1
        else:
            taxId = giToTax[gi]
        data = [taxId] + data
        return data
    
    def createGiToTax(self,cur):
        print "Generating short GI list to create key of TaxIDs in one db query"
        gis = set()
        giToTax = {}
        for line in self.genLine():
            data = line.split(self.delimiter)
            gi = data[1].split("|")[1]
            gis.add(gi)
        gis = "("+str(gis).lstrip("set([").rstrip("])")+")"
        cmd = "SELECT * from GiTax_NCBI WHERE gi in "+gis
        cur.execute(cmd)
        key = cur.fetchall()
        for i in key:
            giToTax[int(i[0])]=int(i[1])
        return giToTax

    def importData(self):
        """
        Producer process
        """
        def addCounts(data):
            minEValue = 9999
            for entry in data:
                eValue = float(entry[-2])
                if eValue < minEValue:
                    minEValue = eValue
                    count = 1
                elif eValue == minEValue:
                    count += 1
            
            count = str(1.0/float(count))
        
            for index,entry in enumerate(data):
                eValue = float(entry[-2])
                if eValue == minEValue:
                    data[index].append(count)
                else:
                    data[index].append("0")
                data[index] = tuple(data[index])
        
            return data
        
        
        with TaxDb.onlyCursor("TaxAssessor_Refs") as cur:
            start = time.time()
            giToTax = self.createGiToTax(cur)
            print "Finished retrieving taxIds"
            
            dump = []
            count = 0
            increment = 100000
            name = ""
            dataToDump=[]
            for line in self.genLine():
                data = self.processLine(line,cur,giToTax)
                if data[1] == name:
                    dataToDump.append(data)
                else:
                    if dataToDump:
                        dataToDump = addCounts(dataToDump)
                        dump += dataToDump
                    name = data[1]
                    dataToDump = [data]
                    if count >= increment:
                        self.parent.send(dump)
                        dump = []
                        increment += 100000
                        if count % 1000000 == 0:
                            print count
                count += 1
            if dataToDump:
                dump += addCounts(dataToDump)
            if dump:
                self.parent.send(dump)
            self.parent.send(None)
            self.parent.close()
            end = time.time()
            print (end-start)," seconds spent in importData"
            print count," records processed"
        self.consumer.join()
                

    def createDbTable(self):
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:
            cmd = ("""CREATE TABLE %s (readName     VARCHAR(80) NOT NULL, 
                                       subjectId    VARCHAR(40) NOT NULL,
                                       percentId    FLOAT(12) NOT NULL, 
                                       alignLength  INT(11) NOT NULL, 
                                       nMisMatch    INT(11) NOT NULL, 
                                       nGapOpens    INT(11) NOT NULL, 
                                       qStartPos    INT(11) NOT NULL, 
                                       qEndPos      INT(11) NOT NULL, 
                                       tStartPos    INT(11) NOT NULL, 
                                       tEndPos      INT(11) NOT NULL, 
                                       eValue       FLOAT(12) NOT NULL, 
                                       bitScore     FLOAT(12) NOT NULL, 
                                       taxId        INT(11) NOT NULL, 
                                       contribution FLOAT(12) NOT NULL DEFAULT 0,
                                       readId       INT(11) NOT NULL AUTO_INCREMENT,
                                       INDEX (readName),
                                       INDEX (taxId),
                                       INDEX (contribution),
                                       INDEX (readName,eValue,contribution),
                                       PRIMARY KEY (readId));"""
                                       % ("t"+str(self.uniqueId)))
            cur.execute(cmd)





              
def loadFile(fileName,fileBody,userName):
    inputFile = InputFile(fileName,fileBody,userName)
    
    if inputFile.fileType == "BLAST":
        inputFile = BlastFile(inputFile)
        inputFile.importData()
        #dbTable = TaxPermute.DbTable(inputFile.uniqueId,"BLAST")
        #dbTable.updateCount()
        TaxTree.createTree(userName,fileName,inputFile.uniqueId)
        return True
    else:
        warnings.warn("UNKNOWN FILETYPE! DELETING")
        return False


def main(fileName):
    fileString = ""
    with open(fileName,"r") as inFile:
        for line in inFile:
            fileString += line

    inputFile = InputFile("test",fileString,"jallison@colostate.edu")
    
    if inputFile.fileType == "BLAST":
        print "blast found"
        inputFile = BlastFile(inputFile)
        inputFile.importData()
        return True
    else:
        warnings.warn("UNKNOWN FILETYPE! DELETING")
        return False


if __name__ == "__main__":
    main(sys.argv[1])



















