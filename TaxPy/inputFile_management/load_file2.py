#!/usr/bin/python

import TaxPy.db_management.db_wrap as TaxDb
import re
import time

class InputFile():
    """Class to extract file information and prepare it to be formed into a
    tree as well as imported into the database.
    """
    def __init__(self,fileName,fileBody,userName,loadOptions):
        self.fileName    = fileName
        self.fileBody    = self.prepFileBody(fileBody)
        self.userName    = userName
        self.loadOptions = loadOptions
        self.reads       = {}
        self.seqIds      = set()
        self.taxIds      = {}
        self.seqIdToTax  = {}
        self.taxIdParent = {}

    def prepFileBody(self,fileBody):
        try:
            return fileBody.splitlines()
        except Exception:
            return fileBody

    def processData(self):
        """A function that reads the uploaded file and extracts the highest
        alignment(s) for each read.  Once the highest alignments have been
        obtained, two processes are started.  The first preps the data for the
        database import and the second consumes that data and places it into
        the database.
        """
        def getBestAlignmentsPerRead(self):
            """A function that moves through the file and extracts the best
            alignment per read.
            """
            for line in self.fileBody:
                if line[0] == "@":
                    continue
                data = line.split(self.loadOptions["delimiter"])
                seqId = data[self.loadOptions["seqIdIndex"]]
                if  seqId == "*":
                    continue
                if (self.loadOptions["seqIdDelimiter"] and
                        self.loadOptions["seqIdDelimiter"] in seqId):
                    seqId = seqId.split(self.loadOptions["seqIdDelimiter"])
                    seqId = seqId[self.loadOptions["seqIdSubIndex"]]
                try:
                    seqId = int(seqId)
                except ValueError:
                    pass
                readName = str(data[self.loadOptions["readNameIndex"]])
                score = float(data[self.loadOptions["scoreIndex"]])

                if readName in self.loadOptions['contigWeights']:
                    weight = self.loadOptions['contigWeights'][readName]
                else:
                    weight = 1

                if ((readName not in self.reads) or
                        ((self.loadOptions["scorePreference"] == "higher") and
                                (score > self.reads[readName].score)) or
                        ((self.loadOptions["scorePreference"] == "lower") and
                                (score < self.reads[readName].score))):
                    self.reads[readName] = ReadData(readName)
                    self.reads[readName].score = score
                    self.reads[readName].seqIds = set([seqId])
                    self.reads[readName].seqIdCounts = {seqId:1}
                    self.reads[readName].lineAssociatedSeqIds = [seqId]
                    self.reads[readName].wholeLines = [line]
                elif ((score == self.reads[readName].score) and
                        (seqId not in self.reads[readName].seqIds)):
                    self.reads[readName].seqIds.add(seqId)
                    if seqId not in self.reads[readName].seqIdCounts:
                        self.reads[readName].seqIdCounts[seqId] = 1
                    else:
                        self.reads[readName].seqIdCounts[seqId] += 1
                    self.reads[readName].lineAssociatedSeqIds.append(seqId)
                    self.reads[readName].wholeLines.append(line)
                self.reads[readName].weight = weight

        def getTaxIdsFromSeqIds(self):
            """A function that retrieves the taxIds that correspond to the
            seqIds that were extracted from the file. The taxIds are retrieved
            from the TaxAssessor_Refs MySQL database. An issue can occur where
            not all seqIds have a corresponding taxId. This can cause an issue
            downstream when assigning TaxIds to reads. The final for loop in
            this function addresses this problem.
            """
            seqIdString = "("+str(self.seqIds).lstrip("set([").rstrip("])")+")"
            if "." in seqIdString:
                cmd = ("SELECT accessionVersion,taxID from seqIdToTaxId_NCBI "
                        "WHERE accessionVersion in "+seqIdString)
            elif re.search('[a-zA-Z]',seqIdString):
                cmd = ("SELECT accession,taxID from seqIdToTaxId_NCBI "
                        "WHERE accession in "+seqIdString)
            else:
                cmd = ("SELECT gi,taxID from seqIdToTaxId_NCBI "
                        "WHERE gi in "+seqIdString)
            with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                   TaxDb.cursor(db) as cur:
                cur.execute(cmd)
                for data in cur:
                    seqId = data[0]
                    taxId = int(data[1])
                    if taxId == 0:
                        taxId = -1
                    self.taxIds[taxId] = TaxonData()
                    self.taxIds[taxId].readAssociated = True
                    self.seqIdToTax[seqId] = taxId

            for seqId in self.seqIds:
                if seqId not in self.seqIdToTax:
                    self.taxIds[-1] = TaxonData()
                    self.taxIds[-1].readAssociated = True
                    self.seqIdToTax[seqId] = -1


        def getTaxIdRelationships(self):
            """Extract the parents of each TaxId all the way up to the
            root node.  This will be passed into the LCA algorithm for each read
            and utilized to find the common ancestor of each TaxID that the read
            aligned to.  Performing this all at once prevents querying the
            database for every read.  Stores all child:parent and
            parent:children data into the self.taxId dict.  This data is used by
            the LCA algorithm and for building the tree.
            """
            newTaxIds = "("+str([taxId for taxId in self.taxIds]).lstrip("set([").rstrip("])")+")"

            with TaxDb.openDb("TaxAssessor_Refs") as db, \
                    TaxDb.cursor(db) as cur:
                allTaxIds = False
                count = 0
                while not allTaxIds:
                    count += 1
                    if count == 1000:
                        raise Exception
                    cmd = ("SELECT parent,child from taxIdNodes_NCBI where "
                           "child in ")
                    cmd += newTaxIds
                    cur.execute(cmd)
                    newTaxIds = "("
                    for row in cur:
                        parent = int(row[0])
                        child = int(row[1])
                        newTaxIds += "'"+str(row[0])+"',"
                        if parent not in self.taxIds:
                            self.taxIds[parent] = TaxonData()
                        self.taxIds[child].parent = parent
                        self.taxIds[parent].children.add(child)
                    newTaxIds = newTaxIds.rstrip(",")+")"
                    if len(newTaxIds) <= 2:
                        allTaxIds = True

        def getTaxIdGenealogies(self):
            """For LCA, generate the full genealogy for a taxId.  Produces a set
            with all parents all the way up to root.  This is used to determine
            where multiple taxa within a read intersect.
            """
            for taxId in self.taxIds:
                ancestorTaxId = taxId
                while ancestorTaxId != 1 and ancestorTaxId != None:
                    ancestorTaxId = self.taxIds[ancestorTaxId].parent
                    self.taxIds[taxId].genealogy.add(ancestorTaxId)

        def getTaxIdRanks(self):
            """For LCA, extract the ranks of each taxa from the NCBI database.
            To be used to determine the highest ranked ancestor within a read.
            """
            with TaxDb.openDb("TaxAssessor_Refs") as db, \
                    TaxDb.cursor(db) as cur:
                cmd = "SELECT Rank FROM Taxon_Rank WHERE taxID=(%s)"
                for taxId in self.taxIds:
                    cur.execute(cmd,taxId)
                    try:
                        rank = int(cur.fetchone()[0])
                        self.taxIds[taxId].rank = rank
                    except Exception:
                        self.taxIds[taxId].rank = None

        def removeNoCountTaxIds(self):
            for taxId in set(self.taxIds):
                if self.taxIds[taxId].count == 0:
                    parentTaxId = self.taxIds[taxId].parent
                    if parentTaxId:
                        try:
                            self.taxIds[parentTaxId].children.remove(taxId)
                        except KeyError:
                            pass
                    self.taxIds.pop(taxId)

        def aggregateStatsUpTree(self,taxId,contribution,score):
            while True:
                self.taxIds[taxId].count += contribution
                self.taxIds[taxId].sumScore += score
                taxId = self.taxIds[taxId].parent
                if (taxId == None):
                    break

        def getTaxIdNames(self):
            with TaxDb.openDbSS("TaxAssessor_Refs") as db, \
                                           TaxDb.cursor(db) as cur:
                cmd = ("SELECT taxID,name from TaxNames_NCBI where taxId in "+
                    "("+str(self.taxIds.keys()).lstrip("set([").rstrip("])")+")")
                cur.execute(cmd)
                for row in cur:
                    taxId = int(row[0])
                    name = str(row[1])
                    self.taxIds[taxId].name = name

        time0 = time.time()
        getBestAlignmentsPerRead(self)
        time1 = time.time()
        print "Time 0-1:",time1-time0

        #consolidate the seqIds
        for readName in self.reads:
            for seqId in self.reads[readName].seqIds:
                self.seqIds.add(seqId)
            #self.seqIds = self.seqIds.union(self.reads[readName].seqIds)

        time2 = time.time()
        print "Time 1-2:",time2-time1

        getTaxIdsFromSeqIds(self)

        time3 = time.time()
        print "Time 2-3:",time3-time2

        #assign taxIds to reads within reads
        for readName in self.reads:
            for seqId in self.reads[readName].lineAssociatedSeqIds:
                self.reads[readName].lineAssociatedTaxIds.append(
                                                self.seqIdToTax[seqId])
                self.reads[readName].taxIds.add(self.seqIdToTax[seqId])

        time4 = time.time()
        print "Time 3-4:",time4-time3

        getTaxIdRelationships(self)

        time5 = time.time()
        print "Time 4-5:",time5-time4

        if (self.loadOptions["useLca"]):
            getTaxIdGenealogies(self)
            getTaxIdRanks(self)
            for readName in self.reads:
                self.reads[readName].findLowestCommonTaxId(self.taxIds)
                assignedTaxIds = self.reads[readName].assignedTaxIds[0]
                score = self.reads[readName].score
                weight = self.reads[readName].weight
                aggregateStatsUpTree(self,assignedTaxIds,weight,score)
            removeNoCountTaxIds(self)
        else:
            for readName in self.reads:
                self.reads[readName].assignedTaxIds = \
                        self.reads[readName].lineAssociatedTaxIds
                self.reads[readName].contribution=(self.reads[readName].weight/
                                                   self.reads[readName].count())
                for seqId in self.reads[readName].seqId: #use seqId's b/c multiple seqIds could hit a single taxon
                    taxId = self.seqIdToTax[seqId]
                    score = contribution * self.reads[readName].score
                    aggregateStatsUpTree(self,taxId,
                            self.reads[readName].contribution,score)

        time6 = time.time()
        print "Time 5-6:",time6-time5
        getTaxIdNames(self)
        time7 = time.time()
        print "Time 6-7:",time7-time6

        return self.reads,self.taxIds


class TaxonData():
    """A class to encapsulate all attributes that belong to a taxon."""
    def __init__(self):
        self.children = set()
        self.parent = None
        self.rank = None
        self.genealogy = set()
        self.count = 0
        self.sumScore = 0
        self.associatedSeqIdCounts = {}
        self.readAssociated = False
        self.name = "N/A"
    @property
    def aveScore(self):
        return self.sumScore/self.count

class ReadData():
    """A class to encapsulate all attributes that belong to a read."""
    def __init__(self,name):
        self.name = name
        self.score = None
        self.seqIds = set()
        self.seqIdCounts = {}
        self.taxIds = set()
        self.assignedTaxIds = []
        self.wholeLines = []
        self.lineAssociatedSeqIds = []
        self.lineAssociatedTaxIds = []
        self.weight = 0

    def findLowestCommonTaxId(self,allTaxIds):
        """Function to determine the lowest common ancestor of all taxIds
        associated with the read.  Replaces the data within self.taxIds with a
        single taxId (the lowest common ancestor).
        """
        readTaxIdGenealogies = []

        if len(self.taxIds) == 0:
            self.assignedTaxIds = [-1]
        elif len(self.taxIds) == 1:
            self.assignedTaxIds = list(self.taxIds)
        elif len(self.taxIds) > 1:
            for taxId in set(self.taxIds):
                if (None in allTaxIds[taxId].genealogy or
                        len(allTaxIds[taxId].genealogy)) == 1:
                    self.taxIds.remove(taxId)
                    continue
                readTaxIdGenealogies.append(allTaxIds[taxId].genealogy)
            if len(readTaxIdGenealogies) > 1:
                commonTaxIds = {}
                for genealogy in readTaxIdGenealogies:
                    for taxId in genealogy:
                        if taxId in commonTaxIds:
                            commonTaxIds[taxId] += 1
                        else:
                            commonTaxIds[taxId] = 1
                taxIdCounts = commonTaxIds
                commonTaxIds = set()
                for taxId in taxIdCounts:
                    if taxIdCounts[taxId]/float(len(readTaxIdGenealogies)) > 0.75:
                        commonTaxIds.add(taxId)
                highestRank = -999
                for commonTaxId in commonTaxIds:
                    if allTaxIds[commonTaxId].rank > highestRank:
                        self.assignedTaxIds = [commonTaxId]
                        highestRank = allTaxIds[commonTaxId].rank
            elif len(readTaxIdGenealogies) == 0:
                self.assignedTaxIds = [-1]
            else:
                self.assignedTaxIds = list(self.taxIds)

    def count(self):
        return len(self.seqIds)
