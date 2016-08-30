#!/usr/bin/python

import TaxPy.db_management.db_wrap as TaxDb

def main():
    fileName = ("../../setup/database_import/names.dmp")

    with TaxDb.openDb("TaxAssessor_Refs") as db, TaxDb.cursor(db) as cur:
        with open(fileName, "r") as inFile:
            cmd = "INSERT INTO TaxNames_NCBI (taxID,name) VALUES "
            count = 0
            dump = []

            for line in inFile:
                if "scientific name" in line:
                    line = line.rstrip("\t|\n")
                    line = line.split("\t|\t")
                    dump.append((int(line[0]),line[1]))
                    count += 1
                if count == 10:
                    dmpCmd = cmd + str(dump).lstrip("[").rstrip("]")+";"
                    cur.execute(dmpCmd)
                    dump = [] 
                    count = 0
            if count > 0: #get remaining names
                dmpCmd = cmd + str(dump).lstrip("[").rstrip("]")+";"
                cur.execute(dmpCmd)
                dump = []  
        db.commit()


if __name__ == "__main__":
    main()




