#!/usr/bin/python

import json
import timeit
import re
import TaxPy.db_management.db_wrap as TaxDb
from itertools import izip


def retrieveReads(userName,fileName,fileId,parentTaxId,offset):

    print offset
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

    def parserFactory(fileOptions):
        class startEndParser():
            def __init__(self,startIndex,endIndex,delimiter):
                #print "using startEndParser"
                self.startIndex = startIndex
                self.endIndex = endIndex
                self.delimiter = delimiter
            def parseLine(self,line):
                data = line.split(delimiter)
                startPos = int(data[self.startIndex])
                endPos = int(data[self.endIndex])
                if startPos > endPos:
                    return (endPos,startPos)
                else:
                    return (startPos,endPos)

        class startSeqLengthParser():
            def __init__(self,startIndex,lengthIndex,delimiter):
                #print "using startSeqLengthParser"
                self.startIndex = startIndex
                self.lengthIndex = lengthIndex
                self.delimiter = delimiter
            def parseLine(self,line):
                data = line.split(delimiter)
                startPos = int(data[self.startIndex])
                endPos = startPos + int(data[self.lengthIndex])
                return (startPos,endPos)

        class startCigarParser():
            def __init__(self,startIndex,cigarIndex,delimiter):
                #print "using startCigarParser"
                self.startIndex = startIndex
                self.cigarIndex = cigarIndex
                self.delimiter = delimiter
            def parseLine(self,line):
                data = line.split(delimiter)
                startPos = int(data[self.startIndex])
                cigar = data[self.cigarIndex]
                cigar = re.split(r'(\d+)',cigar)
                lengthCharacters = ["M","N","D"]
                seqLength = 0
                for index,character in enumerate(cigar[1:]):
                    if index%2 == 0:
                        length = int(character)
                    elif any(x in character for x in lengthCharacters):
                        seqLength += length
                endPos = startPos + seqLength
                return (startPos,endPos)


        refStartPosIndex = int(fileOptions[0])
        refEndPosIndex = None if fileOptions[1] == None else fileOptions[1]
        seqLengthIndex = None if fileOptions[2] == None else fileOptions[2]
        cigarIndex = None if fileOptions[3] == None else fileOptions[3]
        delimiter = fileOptions[4]

        if refEndPosIndex != None:
            return startEndParser(refStartPosIndex,refEndPosIndex,delimiter)
        elif seqLengthIndex != None:
            return startSeqLengthParser(refStartPosIndex,seqLengthIndex,delimiter)
        elif cigarIndex != None:
            return startCigarParser(refStartPosIndex,cigarIndex,delimiter)
        else:
            raise Exception("Error at defining factory parser")

    with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
        cmd = ("SELECT refStartPosIndex, refEndPosIndex, seqLength, cigarIndex, "
               "delimiter FROM fileOptions WHERE uniqueId=%s;")
        cur.execute(cmd,(fileId[1:]))
        fileOptions = cur.fetchone()
        if fileOptions.count(None) > len(fileOptions)-2:
            raise Exception("Error retrieving file options")
        else:
            parser = parserFactory(fileOptions)
            if not parser:
                return False

    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, \
                             TaxDb.cursor(db) as cur:
        reads = []
        readStarts = []
        readEnds = []
        names = []
        cmd = ("SELECT readLine FROM "+fileId+" WHERE seqId=%s AND "
                "taxId=%s")
        time1 = timeit.default_timer()
        cur.execute(cmd, (seqId, taxId))
        time2 = timeit.default_timer()
        time = (time2-time1)
        print time,"seconds in db"
        for line in cur:
            read = {}
            read["startPos"],read["endPos"] = parser.parseLine(line[0])
            read["name"] = "blah"
            read["score"] = 0
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

    time5 = timeit.default_timer()
    time = (time5-time4)
    print time,"seconds creating coverage arrays"

    # depth = 0
    # endPos = -1
    # allDepthsAssigned = False
    # depthAssignedReads = []
    #
    # while not allDepthsAssigned:
    #     depth += 1
    #     endPos = -1
    #     readsToRemove = []
    #     allDepthsAssigned = True
    #     for index,read in enumerate(reads):
    #         if ((read["startPos"] > endPos) and (read["depth"] == -1)):
    #             read["depth"] = depth
    #             endPos = read["endPos"]
    #             depthAssignedReads.append(read)
    #             readsToRemove.append(index)
    #         elif read["depth"] == -1:
    #             allDepthsAssigned = False
    #     for index in reversed(readsToRemove):
    #         del reads[index]
    #
    #
    #
    # time6 = timeit.default_timer()
    # time = (time6-time5)
    # print time,"seconds assigning read depths"

    #data = json.dumps({"readData":depthAssignedReads,"startPos":startPos,"endPos":endPos,
#                       "coverageData":coverageData})

    data = json.dumps({"coverageData":coverageData})
    return data

def getGiCount(userName,fileName,fileId,seqId):

    cmd = "select accessionVersion,gi from seqIdToTaxId_NCBI where gi=%s or accessionVersion=%s;"
    with TaxDb.openDbSS("TaxAssessor_Refs") as db, TaxDb.cursor(db) as cur:
        cur.execute(cmd,(seqId,seqId));
        data = cur.fetchone()

    accessionVersion = data[0]
    gi = data[1]
    selectedReadNames = {}

    cmd = "SELECT readName,taxId FROM "+fileId+" WHERE seqId IN ( %s, %s );"
    with TaxDb.openDbSS("TaxAssessor_Alignments") as db, TaxDb.cursor(db) as cur:
        cur.execute(cmd,(accessionVersion,gi));
        for line in cur:
            readName = line[0]
            taxId = int(line[1])
            if readName in selectedReadNames:
                selectedReadNames[readName].append(taxId)
            else:
                selectedReadNames[readName] = [taxId]

        taxIds = {}
        for readName in selectedReadNames:
            contribution = 1/len(selectedReadNames[readName])
            for taxId in selectedReadNames[readName]:
                if taxId in taxIds:
                    taxIds[taxId] += contribution
                else:
                    taxIds[taxId] = contribution
        return json.dumps(taxIds)
