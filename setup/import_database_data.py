#!/usr/bin/python
import TaxPy.db_management.db_wrap as TaxDb
import os



if __name__ == "__main__":
    
    seqIdFiles=["nucl_est.accession2taxid",
                "nucl_gb.accession2taxid",
                "nucl_gss.accession2taxid",
                "nucl_wgs.accession2taxid",
                "prot.accession2taxid"]
                
    for fileName in seqIdFiles:
        with TaxDb.openDb("TaxAssessor_Refs") as db, TaxDb.cursor(db) as cur:
            cmd = ("INSERT INTO seqIdToTaxId_NCBI (accession,accessionVersion,"
                   "taxId,gi) VALUES ")
            insertData = []
            count = 0
            with open("database_import/"+fileName,"r") as inFile:
                for line in inFile:
                    if count == 0:
                        continue
                    line = line.strip()
                    line = line.split("\t")
                    print line
                    exit()
                
            