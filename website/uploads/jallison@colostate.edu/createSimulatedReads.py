#!/usr/bin/python

import os.path
import sys

"""
createSimulatedReads.py: 

A bioinformatics script that will accept any number of databases 
in fasta format and output all sequences of length greater than
readLength as reads of length readLength. The sequences are divided
up via a moving window of size readLength starting at the first
nucleotide (or amino acid) and terminating at the 
sequenceLength-readLength^th nucleotide.

Inputs:
    Command line arguments:
        -i (file input, can input multiple files)
        -o (file output, defaults to out.fasta)
        -readLength (simulated read length, defaults to 100)

Outputs:
    FASTA file with identifier ">Read #" and read of length readLength
"""



class InputFiles():
    """Contains the file names of the input files"""
    def __init__(self,files):
        self.files = files

class InputFile():
    """For each input file, allow the file to be parsed via a
    generator"""
    def __init__(self,name):
        self.name = name
        self.size = os.path.getsize(name)
    def readSeqs(self):
        """The input file's generator that reads the file line by line
        and yields n multiline sequence as a single string"""
        seq = ""
        with open(self.name,"r") as inFile:
            for line in inFile:
                if ">" in line and len(seq) == 0:
                    pass
                elif ">" in line and len(seq) > 0:
                    seqReturn = seq
                    seq = ""
                    self.updateProgress(inFile.tell())
                    yield seqReturn
                else:
                    seq += line.rstrip("\n")
    def updateProgress(self,bytes):
        progress = (float(bytes)/float(self.size))*100
        sys.stdout.write('\r {0:0.1f}% done'.format(progress))
        sys.stdout.flush()

class OutputFile():
    """For the output file, create a write statement that
    will wrap the output to x characters long as well as 
    incrementally ID the read being written"""
    def __init__(self,name):
        self.name = name
        self.openFile = open(name,"w")
        self.seqNum = 0
    def writeRead(self,line):
        idLine = ">Read_"+str(self.seqNum)+"\n"
        self.seqNum += 1
        self.openFile.write(idLine)
        if len(line)>80:
            count = 0
            while count < len(line):
                outLine = line[count:count+80]
                self.openFile.write(outLine+"\n")
                count += 80
        else:
            self.openfile.write(line)
    def closeFile(self):
        self.openFile.close()

def generateReadFromSequence(seq,readLength):
    """Given a sequence, generate reads from the sequence via
    a moving window of length: readLength"""
    read = ""
    for position in xrange(len(seq)-readLength):
        read = seq[position:position+readLength]
        yield read

def getListUntil(argv):
    """Given a list, return the entries that appear before an
    entry with a leading '-'"""
    shortArgv = []
    for argument in argv:
        if "-" not in argument:
            shortArgv.append(argument)
        else:
            break
    return shortArgv

def getCommandLineArguments(argv):
    """Given command line arguments, determine the file inputs
    (entries after '-i'), file output (entry after -o), and the 
    read length (entry after -readLength).  If arguments are missing,
    give an error or set default values (depending on the argument)"""
    errOut = "Required arguments: -i (file input) and -o (file output)"
    inputFiles = []
    outputFile = []
    readLength = 0
    if len(argv) > 0:
        for pos in xrange(len(argv)):
            if argv[pos] == "-o":
                outputFile = argv[pos+1]
                print "Output File: ",outputFile
            elif argv[pos] == "-i":
                inputFiles = getListUntil(argv[pos+1:])
                #print "Input Files: ",inputFiles
            elif argv[pos] == "-readLength":
                readLength = int(argv[pos+1])
                print "Read length: ",readLength
    else:
        print "No files given"
        print errOut
        exit()

    if len(inputFiles) == 0:
        print "No input file(s) given"
        print errOut
        exit()
    else:
        tempFiles = []
        for checkFile in inputFiles:
            if not os.path.isfile(checkFile):
                print "File does not exist: ",checkFile
                exit()
            else:
                tempFiles.append(InputFile(checkFile))
        inputFiles = tempFiles
    
    if len(outputFile) == 0:
        print "No output file given, defaulting to 'out.fasta'"
        outputFile = 'out.fasta'

    if readLength == 0:
        readLength = 100
        print "Default read length set: ",readLength

    return (InputFiles(inputFiles),OutputFile(outputFile),readLength)

def main(argv):
    (inputFiles,outputFile,readLength) = getCommandLineArguments(argv)
    for file in inputFiles.files:
        for sequence in file.readSeqs():
            if len(sequence)>readLength:
                for read in generateReadFromSequence(sequence,readLength):
                    outputFile.writeRead(read)
    print ""
    outputFile.closeFile()

if __name__ == "__main__":
    main(sys.argv[1:])

