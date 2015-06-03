#!/usr/bin/python
import TaxPy.db_management.db_wrap as TaxDb








def main():
    with TaxDb.openDb("TaxAssessor_Refs") as db:
        with open("setup_node_table.sql","r") as inFile:
            try:
                cur = db.cursor()
                cur.execute(inFile.read())
                cur.close()
            except Exception:
                pass
        
        filename = "../../../resources/nodes.dmp"    
        with open(filename,"r") as inFile:
            cmd = "INSERT INTO taxIdNodes_NCBI (child,parent) VALUES "
            count = 0
            dump = []
            for line in inFile:
                count += 1
                line = line.split("|")
                child = int(line[0])
                parent = int(line[1])
                dump.append((child,parent))
                if count % 100000 == 0:
                    dmpCmd = cmd + str(dump).lstrip("[").rstrip("]")+";"
                    cur = db.cursor()
                    cur.execute(dmpCmd)
                    cur.close()
                    dump = []
        db.commit()





if __name__ == "__main__":
    main()
