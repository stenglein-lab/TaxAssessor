#!/usr/bin/python

import TaxPy.db_management.db_wrap as TaxDb
import time
import json
import os

from collections import OrderedDict

class TaxTree():
    def __init__(self):
        self.children = {}
        self.rank = {}

    def loadChildren(self):
        print "Reading dmp file"
        nodeDmp = "../../../resources/nodes.dmp"
        with open(nodeDmp,"r") as nodeFile:
            for line in nodeFile:
                line = line.split("\t|\t")
                parent = int(line[1])
                child = int(line[0])
                if parent == child:
                    continue
                elif parent in self.children:
                    self.children[parent].append(child)
                else:
                    self.children[parent] = [child]

    def stitchNodes(self,taxId,rank=0):
        rank += 1
        tempTree = OrderedDict({"name":taxId,"rank":rank})
        self.rank[taxId] = rank
        if taxId in self.children:
            children = self.children[taxId]
            tempTree["children"] = [self.stitchNodes(child,rank) for 
                                    child in children]
        return tempTree

def main():
    start = time.time() 

    fullPhyloTree = TaxTree()
    fullPhyloTree.loadChildren() 
    print "Creating tree"
    fullTree = fullPhyloTree.stitchNodes(1)

    end = time.time()
    print (end-start),"seconds building tree"

    print "Creating Database"
    with TaxDb.openDb("TaxAssessor_Refs") as db, TaxDb.cursor(db) as cur:
        try:
            cmd = "DROP TABLE Taxon_Rank;"
            cur.execute(cmd)
        except Exception:
            pass

        start = time.time()
        cmd = """CREATE TABLE Taxon_Rank (taxId INT(20) NOT NULL,
                                          rank  INT(20) NOT NULL,
                                          PRIMARY KEY (taxId));"""
        cur.execute(cmd)
        cmd = "INSERT INTO Taxon_Rank (taxId,rank) VALUES (%s,%s);"
        dumpCount = 0
        for taxId in fullPhyloTree.rank:
            cur.execute(cmd,(taxId,fullPhyloTree.rank[taxId]))
            dumpCount += 1
            if dumpCount % 10000 == 0:
                db.commit()
        cmd = "INSERT INTO Taxon_Rank (taxId,rank) VALUES (-1,2);"
        cur.execute(cmd)
        db.commit()

        end = time.time()
        print (end-start),"seconds importing tree"




if __name__ == "__main__":
    main()







