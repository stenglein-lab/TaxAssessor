#!/usr/bin/python

import os.path
"""
Generic file loading class
"""

class InputFile():
    def __init__(self,fileName):
        self.fileName = self.checkFileExists(fileName)
    def genLine(self,fileName=None,printProgress=False):
        if fileName == None:
            fileName = self.fileName
        with open(fileName,"r") as inFile:
            count = 0
            for line in inFile:
                count += 1
                if printProgress and count == 5000000:
                    count = 0
                    self.progressUpdate(fileName,inFile.tell())
                yield line
    def checkFileExists(self,fileName):
        if not os.path.isfile(fileName):
            raise IOError(fileName+" does not exist")
        else:
            return fileName
    def progressUpdate(self,fileName,currentPos):
        totalSize = os.path.getsize(fileName)
        progress = 100*(float(currentPos)/float(totalSize))
        print "Total progress: %i / %i (%.5f percent)" % (currentPos,totalSize,progress)

