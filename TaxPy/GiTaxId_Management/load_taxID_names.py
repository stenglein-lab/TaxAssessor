#!/usr/bin/python

import InputFile as infl
import TaxDb

"""
load_taxID_names.py - 

When instantiated, utilize .getNames() to load the dictionary, .taxIdToNames,
which contains the taxIDs and names as key and value respectively.  If run as
itself, it will create a database table named 'TaxNames' and load it with the
information with TaxIDs as the index. (Uses TaxDb library)
"""


class TaxIdInfo(infl.InputFile):
    def __init__(self):
        self.fileName = ("../../setup/database_import/names.dmp")
        self.taxIdToNames = {}
    def getNames(self):
        print "Loading TaxID Name Information"
        for line in self.genLine(printProgress=True):
            if "scientific name" in line:
                line = line.rstrip("\t|\n")
                line = line.split("\t|\t")
                self.taxIdToNames[int(line[0])] = line[1]

def main():
    exit()
    taxIdFile = TaxIdInfo()
    taxIdFile.getNames()


    print "Checking name max length"
    maxLen = 0
    for taxId in taxIdFile.taxIdToNames:
        name = taxIdFile.taxIdToNames[taxId]
        if len(name) > maxLen:
            maxLen = len(name)
    print "Name max length = "+str(maxLen)

    taxNameTable = TaxDb.MySqlTable("TaxNames")
    taxNameTable.createTable({"taxID":"int(11) NOT NULL",
                              "name":"varchar("+str(maxLen)+") NOT NULL"},
                              index="taxID")

    count = 0
    fields = ['taxID','name']
    importData = []
    print "Loading taxID-Names into table"
    nRecords = len(taxIdFile.taxIdToNames)
    for taxId in taxIdFile.taxIdToNames:
        count += 1
        name = taxIdFile.taxIdToNames[taxId]
        importData.append((int(taxId),name))
        if count % 100000 == 0:
            print str(count)+"/"+str(nRecords)+" records imported"
            taxNameTable.addItems(fields,importData)
            importData = []
    taxNameTable.addItems(fields,importData)
    taxNameTable.close()
    return


if __name__ == "__main__":
    main()




