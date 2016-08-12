#!/usr/bin/python

import json
import timeit
import re
import TaxPy.db_management.db_wrap as TaxDb
from itertools import izip


def retrieveReads(userName,fileName,fileId,parentTaxId,query):

    time1 = timeit.default_timer()
    taxTree = loadTaxTree(userName,fileName)
    time2 = timeit.default_timer()
    print str(time2-time1)+" seconds loading tree"
    status,subTree = findSubTree(taxTree,parentTaxId)
    time3 = timeit.default_timer()
    print str(time3-time2)+" finding subtree"
    children = findChildren(subTree,[])
    time4 = timeit.default_timer()
    print str(time4-time3)+" finding children"
    readLines,status = getReadLines(children,fileId,query)
    time5 = timeit.default_timer()
    print str(time5-time4)+" getting read lines"

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


def getReadLines(children,fileId,query):
    readLines = []
    count = 0
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                                 TaxDb.cursor(db) as cur:

        cmd = "SELECT COUNT(*) FROM "+fileId+" WHERE taxId IN "
        children = "("+str(children).lstrip("[").rstrip("]")+")"
        cmd += children
        cur.execute(cmd)
        nRows = cur.fetchall()[0][0]

        cmd = "SELECT "+query+" FROM "+fileId+" WHERE taxId IN "
        cmd += children + ";"
        cur.execute(cmd)
        for line in cur:
            readLines.append(line[0])

    return readLines,str(nRows)

def getReadsForTaxIds(userName,fileName,fileId,taxIds,query):
    readLines = []
    count = 0
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                                 TaxDb.cursor(db) as cur:

        cmd = "SELECT "+query+" FROM "+fileId+" WHERE taxId IN (%s)"

        in_p=', '.join(map(lambda x: '%s', taxIds))
        cmd = cmd % in_p

        cur.execute(cmd,taxIds)
        for line in cur:
            readLines.append(line[0])

    return readLines

def getReadsForGiInTaxId(userName,fileName,fileId,taxId,seqId,query):
    readLines = []
    count = 0
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                                 TaxDb.cursor(db) as cur:

        cmd = "SELECT "+query+" FROM "+fileId+" WHERE taxId=%s AND seqId=%s"

        cur.execute(cmd,(taxId,seqId))
        for line in cur:
            readLines.append(line[0])

    return readLines
