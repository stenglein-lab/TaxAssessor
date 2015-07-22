#!/usr/bin/python

import json
import TaxPy.db_management.db_wrap as TaxDb


def retrieveReads(userName,fileName,fileId,parentTaxId):

    taxTree = loadTaxTree(userName,fileName)
    
    found,subTree = findSubTree(taxTree,parentTaxId)
    
    children = findChildren(subTree,[])
    
    readLines,status = getReadLines(children,fileId)

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


def getReadLines(children,fileId):
    readLines = []
    count = 0
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                                 TaxDb.cursor(db) as cur:
        cmd = "SELECT readLine from "+fileId+" where taxId in "
        children = "("+str(children).lstrip("[").rstrip("]")+") LIMIT 1000"
        cmd += children
        cur.execute(cmd)
        for line in cur:
            count += 1
            readLines.append(line[0])
            if count == 1000:
                status = "Too many results, showing first 1000"
                return readLines,status
    status = str(count)+" alignments"
    return readLines,status









