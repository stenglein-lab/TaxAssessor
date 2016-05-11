import multiprocessing
import TaxPy.db_management.db_wrap as TaxDb

class DbImport():
    def __init__(self,reads,fileName,userName):
        self.reads = reads
        self.fileName = fileName
        self.userName = userName
        self.dbTableName = self.getTableName()
        
        
    def getTableName(self):
        with TaxDb.openDb("TaxAssessor_Users") as db, TaxDb.cursor(db) as cur:
            cmd = """SELECT uniqueId from files where 
                     filename=%s and username=%s;"""
            cur.execute(cmd,(self.fileName,self.userName))
            id = int(cur.fetchone()[0])
        return "t"+str(id)

    def createDbTable(self):
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:
            cmd = ("""CREATE TABLE %s (readName     VARCHAR(50) NOT NULL, 
                                       score        FLOAT(11) NOT NULL,
                                       seqId        VARCHAR(32) NOT NULL,
                                       taxId        INT(11) NOT NULL,
                                       readLine     VARCHAR(210) NOT NULL,
                                       INDEX (taxId),
                                       INDEX (taxId,seqId),
                                       INDEX (score));"""
                                       % (self.dbTableName))
            cur.execute(cmd)

    def importDataIntoDb(self):
        with TaxDb.openDb("TaxAssessor_Alignments") as db, \
                                   TaxDb.cursor(db) as cur:   
            cmd = ("""INSERT INTO %s (readName,score,seqId,taxId,
                      readLine) VALUES """ % (self.dbTableName))
            cur.execute("START TRANSACTION;")
            cur.execute("SET autocommit=0;")
            dump = []

            for readName in self.reads:
                for i,line in enumerate(self.reads[readName].wholeLines):
                    try:
                        dump.append((readName,
                                     self.reads[readName].score,
                                     self.reads[readName].lineAssociatedSeqIds[i],
                                     self.reads[readName].assignedTaxIds[i],
                                     line))
                    except IndexError:
                        dump.append((readName,
                                     self.reads[readName].score,
                                     self.reads[readName].lineAssociatedSeqIds[i],
                                     self.reads[readName].assignedTaxIds[0],
                                     line))                   
                    if len(dump) == 10000:
                        dump = str(dump).rstrip("]").lstrip("[")
                        dump = cmd + dump + ";"
                        cur.execute(dump)
                        db.commit()
                        dump = []
            if len(dump) > 0:
                dump = str(dump).rstrip("]").lstrip("[")
                dump = cmd + dump + ";"
                cur.execute(dump)
                db.commit()
            
            
            
            