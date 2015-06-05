#!/usr/bin/python

import re
import sys
import warnings
import MySQLdb
import TaxPy.db_management.db_wrap as TaxDb
import TaxPy.db_management.permute_db_table as TaxPermute
import TaxPy.data_processing.create_tree_quick as TaxTree
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
            
    def importData(self):
        warnings.warn("NOT YET IMPLEMENTED FOR THIS FILETYPE")

class BlastFile(InputFile,FileTemplate):
    def __init__(self,InputFile):
        self.fileName  = InputFile.fileName
        self.fileBody  = InputFile.fileBody
        self.delimiter = InputFile.delimiter
        self.userName  = InputFile.userName
        self.giToTax = None
    
    def importData(self):
        gis = set()
        taxIds = set()
        giToTax = {}
        
        for line in self.genLine():
            data = line.split(self.delimiter)
            gi = int(data[1].split("|")[1])
            if gi not in gis: 
                gis.add(gi)
                
        gis = "("+str(gis).lstrip("set([").rstrip("])")+")"
        cmd = "SELECT gi,taxID from GiTax_NCBI WHERE gi in "+gis
        with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                               TaxDb.cursor(db) as cur:
            cur.execute(cmd)
            for data in cur:
                gi = int(data[0])
                taxId = int(data[1])
                giToTax[gi] = taxId
                if taxId not in taxIds: 
                    taxIds.add(taxId)
        
        self.giToTax = giToTax
        return taxIds
         
         
def loadFile(fileName,fileBody,userName):
    inputFile = InputFile(fileName,fileBody,userName)
    
    if inputFile.fileType == "BLAST":
        inputFile = BlastFile(inputFile)
        taxIds = inputFile.importData()
        taxTree = TaxTree.createTree(taxIds)
        with open("uploads/"+userName+"/"+fileName+".json","w") as outFile:
            outFile.write(taxTree)
        return True
    else:
        warnings.warn("UNKNOWN FILETYPE! DELETING")
        return False
















