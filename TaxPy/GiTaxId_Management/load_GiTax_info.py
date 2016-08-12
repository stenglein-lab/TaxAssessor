#!/usr/bin/python

import MySQLdb
import multiprocessing

from contextlib import closing

"""
load_gi_to_taxID.py - 

Generates GIs and corresponding TaxIDs.  When instantiated, utilize genNucl or
genProt to yield the line from the respective dmp.  If run on its own, it will
create database table giTax with gi and taxID with gi as the index (uses TaxDb
library).
"""

class GiToTax():
    def __init__(self):
        self.path = "/home/jallison/TaxAssessor/resources/"
        self.fileName = self.path+"giTaxId_NCBI_2.dmp"
        self.dbName = "TaxAssessor_Refs"
        self.tableName = "GiTax_NCBI"
        self.connectToDatabase()
        self.pool = []
        self.numThreads = 1
        self.tasks = multiprocessing.JoinableQueue()
        for i in xrange(self.numThreads):
            p = multiprocessing.Process(target=self.importLines,args=(self.tasks,))
            p.start()
            self.pool.append(p)

    def connectToDatabase(self):
        """ 
        Connects to MySQL database.  If database does not exist, create the
        database by reading in sql setup file "db_setup.sql".  Always drops the
        table if it already exists.
        """
        try:
            db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",
                    db=self.dbName)
            db.close()
        except MySQLdb.OperationalError:
            db = MySQLdb.connect(user="taxassessor",passwd="taxassessor")
            with open("setup_giTax_table.sql","r") as sqlFile, closing(db.cursor()) as cur:
                cur.execute(sqlFile.read())
            db.close()

    def giAndTaxId(self,line): 
        line = line.rstrip("\n").split("\t")
        gi = line[0]
        taxID = line[1]
        return gi,taxID

    def importLines(self,in_queue):
        db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",
                db=self.dbName)
        while True:
            lines = in_queue.get()
            if lines == None:
                print "Exiting"
                db.close()
                return
            cmd = "INSERT INTO GiTax_NCBI (gi,taxID) VALUES "
            lines = str(lines)
            lines = lines.lstrip("[").rstrip("]")
            cmd += lines
            cur = db.cursor()
            cur.execute(cmd)
            cur.close()
            db.commit()
            in_queue.task_done()

    def performImport(self):
        print "Importing GiTax table"
        count = 0
        dump = []
        procCount = 0
        with open(self.fileName,"r") as inFile:
            for line in inFile:
                count += 1
                dump.append(self.giAndTaxId(line))
                if count % 100000 == 0:
                    self.tasks.put(dump)
                    dump = []
                    procCount += 1
                    if procCount == self.numThreads*5:
                        print count
                        procCount = 0
                        self.tasks.join()
            if len(dump) > 0:
                self.tasks.put(dump)
        self.tasks.join()
        for i in xrange(self.numThreads):
            self.tasks.put(None)

class TaxNames():
    def __init__(self):
        self.path = "/home/jallison/TaxAssessor/resources/"
        self.fileName = self.path+"names.dmp"
        self.dbName = "TaxAssessor_Refs"
        self.tableName = "TaxNames_NCBI"
        self.connectToDatabase()
        self.pool = []
        self.numThreads = 1
        self.tasks = multiprocessing.JoinableQueue()
        for i in xrange(self.numThreads):
            p = multiprocessing.Process(target=self.importLines,args=(self.tasks,))
            p.start()
            self.pool.append(p)

    def connectToDatabase(self):
        """ 
        Connects to MySQL database.  If database does not exist, create the
        database by reading in sql setup file "db_setup.sql".  Always drops the
        table if it already exists.
        """
        try:
            db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",
                    db=self.dbName)
            db.close()
        except MySQLdb.OperationalError:
            db = MySQLdb.connect(user="taxassessor",passwd="taxassessor")
            with open("setup_giTax_table.sql","r") as sqlFile, closing(db.cursor()) as cur:
                cur.execute(sqlFile.read())
            db.close()

    def importLines(self,in_queue):
        db = MySQLdb.connect(user="taxassessor",passwd="taxassessor",
                db=self.dbName)
        while True:
            lines = in_queue.get()
            if lines == None:
                print "Exiting"
                db.close()
                return
            cmd = "INSERT INTO TaxNames_NCBI (taxID,name) VALUES "
            lines = str(lines)
            lines = lines.lstrip("[").rstrip("]")
            cmd += lines
            cur = db.cursor()
            cur.execute(cmd)
            cur.close()
            db.commit()
            in_queue.task_done()

    def getTaxName(self,line):
        if "scientific name" in line:
            line = line.rstrip("\t|\n")
            line = line.split("\t|\t")
            taxId = int(line[0])
            name = str(line[1])
            return taxId,name
        else:
            return None,None

    def performImport(self):
        print "Importing TaxID/Name table"
        count = 0
        dump = []
        procCount = 0
        with open(self.fileName,"r") as inFile:
            for line in inFile:
                count += 1
                taxId,name = self.getTaxName(line)
                if name != None:
                    dump.append(self.getTaxName(line))
                if count % 100000 == 0:
                    self.tasks.put(dump)
                    dump = []
                    procCount += 1
                    if procCount == self.numThreads*5:
                        print count
                        procCount = 0
                        self.tasks.join()
            if len(dump) > 0:
                self.tasks.put(dump)
        self.tasks.join()
        for i in xrange(self.numThreads):
            self.tasks.put(None)


def main():
    giToTax = GiToTax()
    giToTax.performImport()

    taxNames = TaxNames()
    taxNames.performImport()







    return

if __name__ == "__main__":
    main()



