#!/usr/bin/python

import json
import timeit
import TaxPy.db_management.db_wrap as TaxDb
from itertools import izip


def retrieveReads(userName,fileName,fileId,parentTaxId,offset):

    taxTree = loadTaxTree(userName,fileName)
    found,subTree = findSubTree(taxTree,parentTaxId)
    children = findChildren(subTree,[])
    readLines,status = getReadLines(children,fileId,offset)

    return readLines,status


def findSubTree(tree,parentTaxId,found=False):
    subTree = None
    if int(tree["taxId"]) == int(parentTaxId) or found:
        return True,tree
  
    try:
        for child in tree["children"]:
            found,subTree = findSubTree(child,parentTaxId)
            if found:
                return True,subTree
    except KeyError:
        pass

    return found,subTree


def findChildren(tree,children):
    children.append(tree["taxId"])
    
    try:
        for child in tree["children"]:
            children = findChildren(child,children)
    except KeyError:
        pass

    return children


def loadTaxTree(userName,fileName):
    jsonFile = "uploads/"+userName+"/"+fileName+"_tree.json"
    with open(jsonFile,"r") as inFile:
        taxTree = json.load(inFile)
    return taxTree


def getReadLines(children,fileId,offset):
    readLines = []
    count = 0
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                                 TaxDb.cursor(db) as cur:
                                 
        cmd = "SELECT COUNT(*) FROM "+fileId+" WHERE taxId IN "
        children = "("+str(children).lstrip("[").rstrip("]")+")"
        cmd += children
        cur.execute(cmd)
        nRows = cur.fetchall()[0][0]
                                                                  
        cmd = "SELECT readLine FROM "+fileId+" WHERE taxId IN "
        cmd += children + " LIMIT 1000 OFFSET "+offset+";"
        cur.execute(cmd)
        for line in cur:
            readLines.append(line[0])
            
    return readLines,str(nRows)

def retrieveGiAssociatedReads(userName,fileName,fileId,seqId,taxId):
    print seqId
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                             TaxDb.cursor(db) as cur:
        reads = []
        readStarts = []
        readEnds = []
        names = []
        cmd = ("SELECT readLine FROM "+fileId+" WHERE seqId="+seqId+" AND "
                "taxId="+taxId)
        time1 = timeit.default_timer()
        cur.execute(cmd)
        time2 = timeit.default_timer()
        time = (time2-time1)
        print time,"seconds in db"
        for line in cur:
            line = line[0].split("\t")
            pos1 = int(line[8])
            pos2 = int(line[9])
            read = {}
            if pos1 > pos2:
                read["startPos"] = pos2
                read["endPos"] = pos1
            else:
                read["startPos"] = pos1
                read["endPos"] = pos2
            read["name"] = line[0]
            read["score"] = float(line[10])
            read["depth"] = -1
            reads.append(read)
        time3 = timeit.default_timer()
        time = (time3-time2)
        print time,"seconds in parsing db results"
                
        startPos = min([read['startPos'] for read in reads])
        endPos = max([read['endPos'] for read in reads])
        reads = sorted(reads, key=lambda k: (k['startPos'],k['startPos']-k['endPos']))

        time4 = timeit.default_timer()
        time = (time4-time3)
        print time,"seconds sorting data"     
        
              
        coverage = {}
        for read in reads:
            for position in xrange(read['startPos'],read['endPos']):
                coverage[position] = coverage.get(position,0) + 1
                coverage[position-1] = coverage.get(position-1,0)
                coverage[position+1] = coverage.get(position+1,0)
        
        positions = coverage.keys()
        coverage = coverage.values()
        sorted_lists = sorted(izip(positions, coverage), 
                              reverse=False, key=lambda x: x[0])
        coverageData = []
        for i in xrange(len(sorted_lists)):
            if ((i > 1) and (i < len(sorted_lists)-1)):
                if ((sorted_lists[i][1] == sorted_lists[i-1][1]) and
                        (sorted_lists[i][1] == sorted_lists[i+1][1])):
                    continue
            coverageData.append({"coverage":sorted_lists[i][1],
                                 "position":sorted_lists[i][0]})
        #positions, coverage = [[x[i] for x in sorted_lists] for i in range(2)]        
        
        time5 = timeit.default_timer()
        time = (time5-time4)
        print time,"seconds creating coverage arrays"

        depth = 0
        endPos = -1
        allDepthsAssigned = False
        depthAssignedReads = []
        
        while not allDepthsAssigned:
            depth += 1
            endPos = -1
            readsToRemove = []
            allDepthsAssigned = True
            for index,read in enumerate(reads):
                if ((read["startPos"] > endPos) and (read["depth"] == -1)):
                    read["depth"] = depth
                    endPos = read["endPos"]
                    depthAssignedReads.append(read)
                    readsToRemove.append(index)
                elif read["depth"] == -1:
                    allDepthsAssigned = False
            for index in reversed(readsToRemove):
                del reads[index]



        time6 = timeit.default_timer()
        time = (time6-time5)
        print time,"seconds assigning read depths"
                    
        data = json.dumps({"readData":depthAssignedReads,"startPos":startPos,"endPos":endPos,
                           "coverageData":coverageData})
        return data






