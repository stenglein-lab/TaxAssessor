#!/usr/bin/python
import sys


class Branch():
    def __init__(self,gis):
        self.gis = gis

class OutputFile():
    def __init__(self,fileName):
        self.fileName = fileName
        self.count = 0
        self.readNameBase = "read"
    def createEntries(self,branch):
        with open(self.fileName,"w") as outFile:
            for gi in branch.gis:
                self.count += 1
                for i in xrange(branch.gis[gi]["count"]):
                    readName = "read"+str(self.count)+"\t"
                    subjectId = "gi|"+gi+"|gb|GARBAGE|\t"
                    stuff = "98.70\t77\t0\t1\t33\t108\t2012\t2088\t"
                    score = branch.gis[gi]["score"]+"\t"
                    line = readName+subjectId+stuff+score+"131\n"
                    outFile.write(line)

def singleLineAdditionTest():
    fileName = "single_line_addition.blast"
    astroViruses = Branch({"224466255":{"count":10,"score":"1e-27"},
                           "299766659":{"count":10,"score":"1e-27"}})
    outFile = OutputFile(fileName)
    outFile.createEntries(astroViruses)
    
    


if __name__ == "__main__":
    singleLineAdditionTest()
    
    
    