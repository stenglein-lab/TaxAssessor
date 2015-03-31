#!/usr/bin/python

from multiprocessing import Process,Pipe
import os.path
import time

class ImportAsyncronousFile():
    def __init__(self,fileName):
        self.fileName = self.checkFileName(fileName)
    def checkFileName(self,fileName):
        if os.path.isfile(fileName):
            return fileName
        else:
            raise IOError(fileName+" does not exist")
    def getLines(self,conn):
        with open(self.fileName,"r") as inFile:
            count = 0
            importData = []
            for line in inFile:
                conn.send(line)
                print "From: "+line
            conn.send("eof")
            print "DONE"
            conn.close()
    def insertIntoArray(self,conn,finalArray=[]):
        data = ""
        while data != "eof":
            data = conn.recv()
            print "To: "+data
            finalArray.append(data)
            time.sleep(0.05)
        print len(finalArray)
        return finalArray


if __name__ == "__main__":
    importFile = ImportAsyncronousFile("../../FromMark/314_all_post_bac_"
                                       "filtered_red.blast")
    parent_conn, child_conn = Pipe()
    p1 = Process(target=importFile.getLines,args=(child_conn,))
    p2 = Process(target=importFile.insertIntoArray,args=(parent_conn,))

    p2.start()
    p1.start()
    p1.join()
    p2.join()



