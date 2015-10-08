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
from collections import Counter

class InputFile():
    def __init__(self,fileName,fileBody,userName,loadOptions):
        self.fileName    = fileName
        self.fileBody    = fileBody
        self.fileType, self.delimiter = self.detectFileAttributes()
        self.userName    = userName
        self.loadOptions = loadOptions
        
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
        self.fileName    = InputFile.fileName
        self.fileBody    = InputFile.fileBody
        self.delimiter   = InputFile.delimiter
        self.userName    = InputFile.userName
        self.loadOptions = InputFile.loadOptions
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
        readMinTaxIds = {}
        
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
                taxIds.add(taxId)
                giToTax[gi] = taxId
        
        #get lowest common ancestor for each read
        for readName in readMinGis:
            for gi in readMinGis[readName]:
                try:
                    if readName not in readMinTaxIds:
                        readMinTaxIds[readName] = set([giToTax[gi]])
                    else:
                        readMinTaxIds[readName].add(giToTax[gi])
                except KeyError: #GI's taxId is unknown
                    if readName not in readMinTaxIds:
                        readMinTaxIds[readName] = set([-1])
                    else:
                        readMinTaxIds[readName].add(-1)

        consensusTaxIds = self.getLowestCommonAncestor(readMinTaxIds,taxIds)
              
        #begin processes that prepare the data and perform the database import
        parent,child = multiprocessing.Pipe()
        p=[]
        p.append(multiprocessing.Process(target=self.consumeDumpIntoDb,
                                         args=(child,)))
        p.append(multiprocessing.Process(target=self.produceDumpForDb,
                                         args=(readMinGis,readMinLines,
                                               readMinScore,readMinCount,
                                               giToTax,parent,consensusTaxIds)))
        for process in p:
            process.start()
        
        #count up the contributions from reads that belong to the same TaxID
        taxIds = set()
        for readName in consensusTaxIds:
            taxId = consensusTaxIds[readName]
            taxIds.add(taxId)
            if taxId in taxCount:
                taxCount[taxId] += 1
            else:
                taxCount[taxId] = 1
        
        #begin process to generate read report
        report = TaxReport.ReadReport(readMinGis,readMinScore,
                                      readMinCount,taxCount,gis) 
        readReport = report.createReport()      
        
        self.giToTax = giToTax
        
        for process in p:
            process.join()
        
        return taxIds,taxCount,readReport
        
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
                                       INDEX (eValue));"""
                                       % (self.dbTableName))
            cur.execute(cmd)
         
    def produceDumpForDb(self,readMinGis,readMinLines,readMinScore,
                        readMinCount,giToTax,conn,readMinLCATaxIds):
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

def loadFile(fileName,fileBody,userName,loadOptions):
    inputFile = InputFile(fileName,fileBody,userName,loadOptions)
    
    if inputFile.fileType == "BLAST":
        inputFile = BlastFile(inputFile)
        taxIds,taxCount,readReport = inputFile.importData()
        taxTree = TaxTree.createTree(taxIds,taxCount)
        with open("uploads/"+userName+"/"+fileName+"_tree.json","w") as outFile:
            outFile.write(taxTree)
        with open("uploads/"+userName+"/"+fileName+"_report.json","w") as outFile:
            outFile.write(readReport)
        return
    else:
        raise Exception("Error: Unknown file type")
        return
















