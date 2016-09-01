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
        with open("database_import/"+fileName,"r") as inFile:
            print fileName