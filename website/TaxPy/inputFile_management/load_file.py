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
import os
from collections import Counter

class InputFile():
    def __init__(self,fileName,fileBody,userName,loadOptions):
        self.fileName    = fileName
        self.fileBody    = fileBody
        self.fileType, self.delimiter = self.detectFileAttributes()
        self.userName    = userName
        self.loadOptions = loadOptions
        
    def genLine(self):
        try:
            inFile = self.fileBody.splitlines()
        except Exception:
            inFile = self.fileBody
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
            try: #BLAST
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
            try: #SAM
                if "@" in firstLine[0]:  #CONTAINS A HEADER
                    if ("@HD" in testLine[0] and
                        "VN"  in testLine[1]):
                        return "SAM",delimiter
                else:   #DOES NOT CONTAIN A HEADER
                    gi = testLine[2].split("|")[1]
                    value = int(testLine[1])
                    value = int(testLine[3])
                    value = int(testLine[4])
                    value = int(testLine[7])
                    value = int(testLine[8])
                    return "SAM",delimiter
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
        
    def getLowestCommonAncestor(self,readMinTaxIds,taxIds):
        taxIds = set(taxIds)  #hacky way of getting around mutable objects being modified by functions
        #get all included taxIds (in the tree)

        newTaxIds = "("+str(taxIds).lstrip("set([").rstrip("])")+")"
        with TaxDb.openDb("TaxAssessor_Refs") as db, TaxDb.cursor(db) as cur:
            allTaxIds = False
            taxIdParent = {}
            while not allTaxIds:
                cmd = "SELECT parent,child from taxIdNodes_NCBI where child in "
                cmd += newTaxIds
                cur.execute(cmd)
                newTaxIds = "("
                for row in cur:
                    newTaxIds += "'"+str(row[0])+"',"
                    parent = int(row[0])
                    child = int(row[1])
                    taxIds.add(parent)
                    taxIdParent[child] = parent
                newTaxIds = newTaxIds.rstrip(",")+")"
                if len(newTaxIds) == 2:
                    allTaxIds = True
        
        #get rank of all included taxIds
        taxIdRank = {}
        taxIdsToRemove = []
        with TaxDb.openDb("TaxAssessor_Refs") as db, TaxDb.cursor(db) as cur:
            cmd = "SELECT Rank FROM Taxon_Rank WHERE taxID=(%s)"
            for taxId in taxIds:
                cur.execute(cmd,taxId)
                try:
                    rank = int(cur.fetchone()[0])
                    taxIdRank[taxId] = rank
                except Exception:
                    taxIdsToRemove.append(taxId)
        for taxId in taxIdsToRemove:
            taxIds.remove(taxId)
        
        #find the lowest common ancestor for each read
        readMinLcaTaxIds = {}
        for readName in readMinTaxIds:
            if len(readMinTaxIds[readName]) > 1:
                taxIdCount = Counter({})
                for taxId in readMinTaxIds[readName]:
                    tempTaxIdCount = Counter({})
                    if taxId == -1:
                        continue
                    atRoot = False
                    while not atRoot:
                        if taxId in tempTaxIdCount:
                            tempTaxIdCount[taxId] += 1
                        else:
                            tempTaxIdCount[taxId] = 1
                        if taxId == 1:
                            atRoot = True
                        else:
                            try:
                                taxId = taxIdParent[taxId]
                            except KeyError: #ISOLATED PORTION OF TREE: NUKE TEMP DATA
                                tempTaxIdCount = Counter({})
                                atRoot = True
                    taxIdCount = taxIdCount + tempTaxIdCount
                
                    consensusCount = 0
                    for taxId in taxIdCount:
                        if taxIdCount[taxId] > consensusCount:
                            consensusCount = taxIdCount[taxId]
                            consensusRank = taxIdRank[taxId]
                            consensusTaxId = taxId

                        elif taxIdCount[taxId] == consensusCount:
                            rank = taxIdRank[taxId]
                            if rank > consensusRank: 
                                consensusTaxId = taxId
                                consensusRank = rank

                    readMinLcaTaxIds[readName] = consensusTaxId
            else:
                (readMinLcaTaxIds[readName],) = readMinTaxIds[readName]


        return readMinLcaTaxIds
                
class BlastFile(InputFile,FileTemplate):
    def __init__(self,InputFile):
        #Basic File Information
        self.fileName      = InputFile.fileName
        self.fileBody      = InputFile.fileBody
        self.delimiter     = InputFile.delimiter
        self.userName      = InputFile.userName
        self.loadOptions   = InputFile.loadOptions
        #Information for building the taxonomy tree & reports
        self.readMinScore  = {}
        self.readMinGis    = {}
        self.readMinTaxIds = {}
        self.readMinCount  = {}
        self.readMinLines  = {}
        self.taxCount      = {}
        self.giToTax       = {}
        self.gis           = set()
        self.taxIds        = set()
        #Setting up database table
        self.checkForDb()
        self.dbTableName   = self.getTableName()

    def importData(self):
        """
        A function that reads the uploaded file and extracts the highest 
        alignment(s) for each read.  Once the highest alignments have been
        obtained, two processes are started.  The first preps the data for the
        database import and the second consumes that data and places it into
        the database.
        """
        def getBestAlignmentsPerRead(self):
            #move through the file extracting the best alignment(s) for each read.
            for line in self.genLine():
                data = line.split(self.delimiter)
                gi = int(data[1].split("|")[1])
                readName = data[0]
                eValue = data[-2]
                
                if ((readName not in self.readMinScore) or
                        (eValue < self.readMinScore[readName])):
                    self.readMinScore[readName] = eValue
                    self.readMinGis[readName] = [gi]
                    self.readMinLines[readName] = [line]
                    self.readMinCount[readName] = 1
                elif eValue == self.readMinScore[readName]:
                    self.readMinGis[readName].append(gi)
                    self.readMinLines[readName].append(line)
                    self.readMinCount[readName] += 1        
        def getTaxIdsFromGis(self):
            #get the TaxIDs from the list of GIs.
            gistring = "("+str(self.gis).lstrip("set([").rstrip("])")+")"
            cmd = "SELECT gi,taxID from GiTax_NCBI WHERE gi in "+gistring
            with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                   TaxDb.cursor(db) as cur:
                cur.execute(cmd)
                for data in cur:
                    gi = int(data[0])
                    taxId = int(data[1])
                    if taxId == 0:
                        taxId = -1
                    self.taxIds.add(taxId)
                    self.giToTax[gi] = taxId   
        def assignTaxIdsToReads(self):
            #get assign taxIds to each read
            for readName in self.readMinGis:
                for gi in self.readMinGis[readName]:
                    try:
                        if readName not in self.readMinTaxIds:
                            self.readMinTaxIds[readName] = set([self.giToTax[gi]])
                        else:
                            self.readMinTaxIds[readName].add(self.giToTax[gi])
                    except KeyError: #GI's taxId is unknown
                        if readName not in self.readMinTaxIds:
                            self.readMinTaxIds[readName] = set([-1])
                        else:
                            self.readMinTaxIds[readName].add(-1)        
        def calcTaxIdContributionsFromReads(consensusTaxIds):
            #count up the contributions from reads that belong to the same TaxID
            if self.loadOptions["useLca"]:
                self.taxIds = set()
                for readName in consensusTaxIds:
                    taxId = consensusTaxIds[readName]
                    self.taxIds.add(taxId)
                    if taxId in self.taxCount:
                        self.taxCount[taxId] += 1
                    else:
                        self.taxCount[taxId] = 1
            else:
                for readName in self.readMinTaxIds:
                    contribution = 1.0/self.readMinCount[readName]
                    for taxId in self.readMinTaxIds[readName]:
                        if taxId in self.taxCount:
                            self.taxCount[taxId] += contribution
                        else:
                            self.taxCount[taxId] = contribution       
       
       
        getBestAlignmentsPerRead(self)
    
        #consolidate the GIs and their contributions (normalized count)
        for readName in self.readMinGis:
            self.gis = self.gis.union(self.readMinGis[readName])
        
        getTaxIdsFromGis(self)
        assignTaxIdsToReads(self)
        consensusTaxIds = self.getLowestCommonAncestor(self.readMinTaxIds,
                                                       self.taxIds)
              
        #begin processes that prepare the data and perform the database import
        parent,child = multiprocessing.Pipe()
        p=[]
        p.append(multiprocessing.Process(target=self.consumeDumpIntoDb,
                                         args=(child,)))
        p.append(multiprocessing.Process(target=self.produceDumpForDb,
                                         args=(self.readMinGis,
                                               self.readMinLines,
                                               self.readMinScore,
                                               self.readMinCount,
                                               self.giToTax,
                                               consensusTaxIds,
                                               parent)))
        for process in p:
            process.start()
            
        calcTaxIdContributionsFromReads(consensusTaxIds)
    
        return p
        
    def createDbTable(self):
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:
            cmd = ("""CREATE TABLE %s (readName     VARCHAR(50) NOT NULL, 
                                       taxId        INT(11) NOT NULL,
                                       count        FLOAT(11) NOT NULL,
                                       eValue       FLOAT(11) NOT NULL,
                                       consensusTaxId INT(11) NOT NULL,
                                       readLine     VARCHAR(210) NOT NULL,
                                       INDEX (consensusTaxId),
                                       INDEX (taxId),
                                       INDEX (eValue));"""
                                       % (self.dbTableName))
            cur.execute(cmd)
         
    def produceDumpForDb(self,readMinGis,readMinLines,readMinScore,
                        readMinCount,giToTax,readMinLCATaxIds,conn):
        countDump = 0
        dump = []
        for readName in readMinGis:
            eValue = readMinScore[readName]
            count = readMinCount[readName]
            consensusTaxId = readMinLCATaxIds[readName]
            for index,gi in enumerate(readMinGis[readName]):
                alignLine = readMinLines[readName][index]
                try:
                    taxId = giToTax[gi]
                except Exception:
                    continue
                countDump += 1
                dump.append((readName,taxId,count,eValue,
                             consensusTaxId,alignLine))
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
            cmd = ("""INSERT INTO %s (readName,taxId,count,eValue,
                      consensusTaxId,readLine) VALUES """ % (self.dbTableName))
            cur.execute("START TRANSACTION;")
            cur.execute("SET autocommit=0;")
            dump = []
            while True:
                dump = conn.recv()
                if dump == None:
                    print "Finished DB Loading"
                    conn.close()
                    return
                else:
                    dump = cmd + dump + ";"
                    cur.execute(dump)
                    db.commit()

class SamFile(InputFile,FileTemplate):
    def __init__(self,InputFile):
        #Basic File Information
        self.fileName    = InputFile.fileName
        self.fileBody    = InputFile.fileBody
        self.delimiter   = InputFile.delimiter
        self.userName    = InputFile.userName
        self.loadOptions = InputFile.loadOptions
        #Information for building the taxonomy tree & reports
        self.readMinScore  = {}
        self.readMinGis    = {}
        self.readMinTaxIds = {}
        self.readMinCount  = {}
        self.readMinLines  = {}
        self.taxCount      = {}
        self.giToTax       = {}
        self.gis           = set()
        self.taxIds        = set()
        #Setting up database table
        self.checkForDb()
        self.dbTableName   = self.getTableName()
        
    def importData(self):
        """
        A function that reads the uploaded file and extracts the highest 
        alignment(s) for each read.  Once the highest alignments have been
        obtained, two processes are started.  The first preps the data for the
        database import and the second consumes that data and places it into
        the database.
        """    
        def getBestAlignmentsPerRead(self):
            #move through the file extracting the best alignment(s) for each read.
            for line in self.genLine():
                if "@" in line[0]: #skip if header section
                    continue
                else:
                    data = line.split(self.delimiter)
                    try:
                        gi = int(data[2].split("|")[1])
                    except IndexError:
                        continue
                    readName = data[0]
                    mapQ = int(data[4])
                    if ((readName not in self.readMinScore) or
                            (mapQ < self.readMinScore[readName])):
                        self.readMinScore[readName] = mapQ
                        self.readMinGis[readName] = [gi]
                        self.readMinLines[readName] = [line]
                        self.readMinCount[readName] = 1
                    elif mapQ == self.readMinScore[readName]:
                        self.readMinGis[readName].append(gi)
                        self.readMinLines[readName].append(line)
                        self.readMinCount[readName] += 1    
        def getTaxIdsFromGis(self):
            #get the TaxIDs from the list of GIs.
            gistring = "("+str(self.gis).lstrip("set([").rstrip("])")+")"
            cmd = "SELECT gi,taxID from GiTax_NCBI WHERE gi in "+gistring
            with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                   TaxDb.cursor(db) as cur:
                cur.execute(cmd)
                for data in cur:
                    gi = int(data[0])
                    taxId = int(data[1])
                    if taxId == 0:
                        taxId = -1
                    self.taxIds.add(taxId)
                    self.giToTax[gi] = taxId   
        def assignTaxIdsToReads(self):
            #get assign taxIds to each read
            for readName in self.readMinGis:
                for gi in self.readMinGis[readName]:
                    try:
                        if readName not in self.readMinTaxIds:
                            self.readMinTaxIds[readName] = set([self.giToTax[gi]])
                        else:
                            self.readMinTaxIds[readName].add(self.giToTax[gi])
                    except KeyError: #GI's taxId is unknown
                        if readName not in self.readMinTaxIds:
                            self.readMinTaxIds[readName] = set([-1])
                        else:
                            self.readMinTaxIds[readName].add(-1)        
        def calcTaxIdContributionsFromReads(consensusTaxIds):
            #count up the contributions from reads that belong to the same TaxID
            if self.loadOptions["useLca"]:
                self.taxIds = set()
                for readName in consensusTaxIds:
                    taxId = consensusTaxIds[readName]
                    self.taxIds.add(taxId)
                    if taxId in self.taxCount:
                        self.taxCount[taxId] += 1
                    else:
                        self.taxCount[taxId] = 1
            else:
                for readName in self.readMinTaxIds:
                    contribution = 1.0/self.readMinCount[readName]
                    for taxId in self.readMinTaxIds[readName]:
                        if taxId in self.taxCount:
                            self.taxCount[taxId] += contribution
                        else:
                            self.taxCount[taxId] = contribution    

        getBestAlignmentsPerRead(self)
        #consolidate the GIs and their contributions (normalized count)
        for readName in self.readMinGis:
            self.gis = self.gis.union(self.readMinGis[readName])
        getTaxIdsFromGis(self)
        assignTaxIdsToReads(self)
        consensusTaxIds = self.getLowestCommonAncestor(self.readMinTaxIds,
                                                       self.taxIds)    
        #begin processes that prepare the data and perform the database import
        parent,child = multiprocessing.Pipe()
        p=[]
        p.append(multiprocessing.Process(target=self.consumeDumpIntoDb,
                                         args=(child,)))
        p.append(multiprocessing.Process(target=self.produceDumpForDb,
                                         args=(self.readMinGis,
                                               self.readMinLines,
                                               self.readMinScore,
                                               self.readMinCount,
                                               self.giToTax,
                                               consensusTaxIds,
                                               parent)))
        for process in p:
            process.start()
            
        calcTaxIdContributionsFromReads(consensusTaxIds)
    
        return p
        
    def createDbTable(self):
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:
            cmd = ("""CREATE TABLE %s (readName     VARCHAR(50) NOT NULL, 
                                       taxId        INT(11) NOT NULL,
                                       count        FLOAT(11) NOT NULL,
                                       mapQ         SMALLINT NOT NULL,
                                       consensusTaxId INT(11) NOT NULL,
                                       readLine     VARCHAR(500) NOT NULL,
                                       INDEX (consensusTaxId),
                                       INDEX (taxId),
                                       INDEX (mapQ));"""
                                       % (self.dbTableName))
            cur.execute(cmd)
            
    def produceDumpForDb(self,readMinGis,readMinLines,readMinScore,
                        readMinCount,giToTax,readMinLCATaxIds,conn):
        countDump = 0
        dump = []
        for readName in readMinGis:
            eValue = readMinScore[readName]
            count = readMinCount[readName]
            consensusTaxId = readMinLCATaxIds[readName]
            for index,gi in enumerate(readMinGis[readName]):
                alignLine = readMinLines[readName][index]
                try:
                    taxId = giToTax[gi]
                except Exception:
                    continue
                countDump += 1
                dump.append((readName,taxId,count,eValue,
                             consensusTaxId,alignLine))
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
            cmd = ("""INSERT INTO %s (readName,taxId,count,mapQ,
                      consensusTaxId,readLine) VALUES """ % (self.dbTableName))
            cur.execute("START TRANSACTION;")
            cur.execute("SET autocommit=0;")
            dump = []
            while True:
                dump = conn.recv()
                if dump == None:
                    print "Finished DB Loading"
                    conn.close()
                    return
                else:
                    dump = cmd + dump + ";"
                    cur.execute(dump)
                    db.commit()
                                                       

                                                       
        
                    
def loadFile(fileName,fileBody,userName,loadOptions):
    inputFile = InputFile(fileName,fileBody,userName,loadOptions)
    
    if inputFile.fileType == "BLAST":
        inputFile = BlastFile(inputFile)
    elif inputFile.fileType == "SAM":
        inputFile = SamFile(inputFile)
        print "SAM filetype recognized"
    else:
        raise Exception("Error: Unknown file type")
        return
    #Once the filetype is set, process the data
    loadIntoDbProc = inputFile.importData()
    taxTree = TaxTree.createTree(inputFile.taxIds,inputFile.taxCount)
    #create the reports
    report = TaxReport.ReadReport(inputFile.readMinGis,inputFile.readMinScore,
                                  inputFile.readMinCount,inputFile.taxCount,
                                  inputFile.gis) 
    readReport = report.createReport()
    #Write tree and reports to files
    this_dir = os.path.dirname(__file__)
    with open(this_dir+"/../../uploads/"+userName+"/"+fileName+"_tree.json","w") as outFile:
        outFile.write(taxTree)
    with open(this_dir+"/../../uploads/"+userName+"/"+fileName+"_report.json","w") as outFile:
        outFile.write(readReport)
        
    #Wait for DB loading to finish
    for process in loadIntoDbProc:
        process.join()
        
    return















