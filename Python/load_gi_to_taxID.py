#!/usr/bin/python

import InputFile as infl
import TaxDb

"""
load_gi_to_taxID.py - 

Generates GIs and corresponding TaxIDs.  When instantiated, utilize genNucl or
genProt to yield the line from the respective dmp.  If run on its own, it will
create database table giTax with gi and taxID with gi as the index (uses TaxDb
library).
"""


class GiToTax(infl.InputFile):
    def __init__(self):
        self.path = ("/Users/jallison/Documents/NCBI-dump/taxonomy/")
        self.fileNames = [self.path+"gi_taxid_nucl.dmp",
                          self.path+"gi_taxid_prot.dmp"]
        self.data = []
    def genNucl(self):
        print "Importing gi-taxID file: "+self.fileNames[0]
        for line in self.genLine(self.fileNames[0],True):
            yield self.giAndTaxId(line)
    def genProt(self):
        print "Importing gi-taxID file: "+self.fileNames[1]
        for line in self.genLine(self.fileNames[1],True):
            yield self.giAndTaxId(line)
    def giAndTaxId(self,line): 
        line = line.rstrip("\n").split("\t")
        gi = line[0]
        taxID = line[1]
        return gi,taxID
    def getTaxIdsFromFiles(self,gis):
        for fileName in self.fileNames:
            print "Checking gi-taxID file: "+fileName
            for line in self.genLine(fileName,True):
                if any(gi in line for gi in gis):
                    line = line.rstrip("\n").split("\t")
                    self.giToTax[line[0]] = line[1]

def main():
    exit() #comment out to run code 
           #(placed as a safety to only build database once)
    giToTax = GiToTax()
    giTaxTable = TaxDb.MySqlTable("giTax")
    giTaxTable.createTable({"gi":"int(11) NOT NULL",
                           "taxID":"int(11) NOT NULL"},
                           index="gi")
    count = 0
    fields = ["gi","taxID"]
    for inFile in [giToTax.genNucl(),giToTax.genProt()]:
        for gi,taxID in inFile:
            data = (int(gi),int(taxID))
            giToTax.data.append(data)
            count += 1
            if count == 100000:
                giTaxTable.addItems(fields,giToTax.data)
                giToTax.data = []
                count = 0
        giTaxTable.addItems(fields,giToTax.data)

    giTaxTable.close()
    return

if __name__ == "__main__":
    main()



