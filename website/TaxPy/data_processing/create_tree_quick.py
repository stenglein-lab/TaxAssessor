#!/usr/bin/python

import TaxPy.db_management.db_wrap as TaxDb
import time
import json
import os

from collections import OrderedDict

class TaxTree():
    def __init__(self,taxIds):
        self.includedTaxIds = taxIds
        self.children = {1:[-1]}
        self.parents = {-1:1}
        self.names = {-1:"Unknown"}

    def getIncludedNodes(self):
        getParents = list(self.includedTaxIds)
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
                        self.includedTaxIds.add(newTaxId)
                if not getParents:
                    print "All nodes retrieved, stitching together tree"
                    break
                    
    def getChildrenDict(self):
        with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                       TaxDb.cursor(db) as cur:
            cmd = ("SELECT child,parent from taxIdNodes_NCBI where child in "+
                "("+str(self.includedTaxIds).lstrip("set([").rstrip("])")+")")
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
                "("+str(self.includedTaxIds).lstrip("set([").rstrip("])")+")")
            cur.execute(cmd)
            for row in cur:
                taxId = int(row[0])
                name = str(row[1])
                self.names[taxId] = name
        
    def stitchNodes(self,nodeName):
        tempTree = OrderedDict({"name":self.names[nodeName],
                                "size":0})
        if nodeName in self.children:
            children = self.children[nodeName]
            tempTree["children"] = [self.stitchNodes(child) for 
                                    child in children]
        return tempTree
        
def createTree(taxIds):
    start = time.time()
    
    taxTree = TaxTree(taxIds)
    taxTree.getIncludedNodes()
    taxTree.getChildrenDict()
    taxTree.getTaxIdNames()
    fullTree = taxTree.stitchNodes(1)    
    fullTree = json.dumps(fullTree,sort_keys=False)
    
    end = time.time()
    print (end-start),"seconds building tree"
    
    return fullTree





