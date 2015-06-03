#!/usr/bin/python

import TaxPy.db_management.db_wrap as TaxDb
import time
import json
import os

from collections import OrderedDict

class TaxTree():
    def __init__(self,userName,fileName,uniqueId):
        self.userName = userName
        self.fileName = fileName
        self.uniqueId = "t"+str(uniqueId)
        self.children = {1:[-1]}
        self.parents = {-1:1}
        self.names = {-1:"Unknown"}
        self.includedTaxIds = {}

    def getStartingTaxIdCount(self):
        with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                                       TaxDb.cursor(db) as cur:
            cur.execute('SELECT taxId,contribution FROM '+self.uniqueId+
                        " WHERE contribution>=0")
            i = 0
            for row in cur:
                i += 1
                taxId = int(row[0])
                contribution = float(row[1])
                if taxId in self.includedTaxIds:
                    self.includedTaxIds[taxId] += contribution
                else:
                    self.includedTaxIds[taxId] = contribution

    def getIncludedNodes(self):
        getParents = self.includedTaxIds.keys()
        with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                       TaxDb.cursor(db) as cur:
            cmd = "SELECT parent from taxIdNodes_NCBI where child in "
            while True:
                getParents = "("+str(getParents).lstrip("[").rstrip("]")+")"
                cur.execute(cmd+getParents)
                getParents = []
                for row in cur:
                    newTaxId = int(row[0])
                    if newTaxId not in self.includedTaxIds:
                        getParents.append(newTaxId)
                        self.includedTaxIds[newTaxId] = 0
                if not getParents:
                    print "All nodes retrieved, stitching together tree"
                    break
                    
    def getFullParentDict(self):
        with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                       TaxDb.cursor(db) as cur:
            cmd = ("SELECT child,parent from taxIdNodes_NCBI where child in "+
                "("+str(self.includedTaxIds.keys()).lstrip("[").rstrip("]")+")")
            cur.execute(cmd)
            for row in cur:
                child = int(row[0])
                parent = int(row[1])
                self.parents[child] = parent
                if parent in self.children:
                    self.children[parent].append(child)
                else:
                    self.children[parent] = [child]
    
    def getTaxIdNames(self):
        with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                       TaxDb.cursor(db) as cur:    
            cmd = ("SELECT taxID,name from TaxNames_NCBI where taxId in "+
                "("+str(self.includedTaxIds.keys()).lstrip("[").rstrip("]")+")")
            cur.execute(cmd)
            for row in cur:
                taxId = int(row[0])
                name = str(row[1])
                self.names[taxId] = name
        
    def stitchNodes(self,nodeName):
        tempTree = OrderedDict({"name":self.names[nodeName],
                                "size":self.includedTaxIds[nodeName]})
        if nodeName in self.children:
            children = self.children[nodeName]
            tempTree["children"] = [self.stitchNodes(child) for 
                                    child in children]
        return tempTree
        
def createTree(userName,fileName,uniqueId):
    start = time.time()
    taxTree = TaxTree(userName,fileName,uniqueId)
    taxTree.getStartingTaxIdCount()
    taxTree.getIncludedNodes()
    taxTree.getFullParentDict()
    taxTree.getTaxIdNames()
    fullTree = taxTree.stitchNodes(1)    
    fullTree = json.dumps(fullTree,sort_keys=False)
        
    with open("uploads/"+userName+"/"+fileName+".json","w") as outFile:
        outFile.write(fullTree)
    
    end = time.time()
    
    print (end-start),"seconds building tree"





