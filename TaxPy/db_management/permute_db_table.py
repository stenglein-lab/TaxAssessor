#!/usr/bin/python

import TaxPy.db_management.db_wrap as TaxDb

import time



class DbTable():
    def __init__(self,uniqueId,fileType):
        self.uniqueId = "t"+str(uniqueId)
        self.fileType = fileType

    def getReadNames(self,cur):
        reads = set()
        cmd = "SELECT DISTINCT readName FROM " + self.uniqueId + ";"
        cur.execute(cmd)
        distinctReads = cur.fetchall()
        for read in distinctReads:
            reads.add(read[0])
        return reads

    def updateCount(self):
        print "Updating counts in DB"
        start = time.clock()
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:
            reads = self.getReadNames(cur)
            for read in reads:
                cmd = ("SELECT eValue,readId FROM "+
                       self.uniqueId+" WHERE readName = '"+read+"';") 
                cur.execute(cmd)
                readMetrics = cur.fetchall()
                
                minEValue = 99999
                bestReads = set()
                for readMetric in readMetrics:
                    eValue = float(readMetric[0])
                    if eValue < minEValue:
                        minEValue = eValue
                        bestReads = set([int(readMetric[1])])
                    elif eValue == minEValue:
                        bestReads.add(int(readMetric[1]))
            
                count = 1.0/len(bestReads)
                for readId in bestReads:
                    cmd = "UPDATE "+self.uniqueId+" SET contribution=%s WHERE readId='"
                    cur.execute(cmd+str(readId)+"';",count)
            db.commit()
        end = time.clock()
        
        print (end-start),"seconds updating counts"


            # cmd = ("""UPDATE {0} 
                    # JOIN (SELECT 
                          # readName AS rId,
                          # MIN(eValue) AS eValue, 
                          # (SELECT 1/COUNT(*) 
                           # FROM {0} 
                           # WHERE readName = rId AND 
                           # eValue = (SELECT MIN(eValue) FROM {0}
                                     # WHERE readName = rId)) AS contribution
                          # FROM {0}
                          # GROUP BY readName) AS NewTable 
                    # ON NewTable.rId = {0}.readName
                    # AND NewTable.eValue = {0}.eValue
                    # SET {0}.contribution = NewTable.contribution;""").format(self.uniqueId)
            # print cmd
            # cur.execute(cmd)

