#!/usr/bin/python

import os.path
import sys
import InputFile as infl
import TaxDb

"""
load_align_file.py - 

Perform alignment file importing.  Given a file name, the
file existance is confirmed as well as the supported extension.  The extension
is then used to determine the file type and how the data is generated.  If the
extension is unrecognized, read the first line of the file and attempt to 
infer the file type.
"""


class AlignmentInputFile(infl.InputFile):
    """
    File input class to check file existence and if the file type is 
    supported.  Can also create a dictionary to keep track how often a GI
    occurs.
    """
    def __init__(self,fileName):
        self.fileName = self.checkFileExists(fileName)
        self.fileType = self.checkFileType(fileName)
        self.giCount = {}
        self.taxCount = {}
    def checkFileType(self,fileName):
        temp,fileExt = os.path.splitext(fileName)
        if fileExt == ".blast":
            fileType = "BLAST"
        elif fileExt == ".sam":
            fileType = "SAM"
        else:
            fileType = self.inferFileType(fileName)
        print fileType+" file detected"
        return fileType
    def inferFileType(self,fileName):
        """
        Reads first line of the file to determine the alignment file type
        """
        err = ("\nUnknown file extension. \nCurrent supported extensions "
               "are '.sam' and '.blast'.")
        #read first line
        with open(self.fileName,"r") as inFile:
            line = inFile.readline()
        tabLine = line.split("\t")

        #check if first line exists
        if len(tabLine) == 0:
            raise IOError(err+"\nCould not parse first line.")
        
        #check if blast file first
        try: 
            for index in xrange(2,12):
                value = float(tabLine[index])
            print "Inferred BLAST file type from first line"
            return "BLAST"
        except ValueError:
            fileType = None

        try: 
            for index in [1,3,4]:
                value = float(tabLine[index])
            print "Inferred SAM file type from first line"
            return "SAM"
        except ValueError:
            fileType = None

        if fileTyle == None:
            raise IOError(err+"\nUnable to determine filetype from line")

    def importAlignmentData(self):
        if self.fileType == "SAM":
            raise IOError("Cannot read SAM files yet")
        if self.fileType == "BLAST":
            print "Importing BLAST file contents"
            for line in self.genLine(printProgress=True):
                data = line.split("\t")
                gi = data[1].split("|")[1]
                if gi not in self.giCount:
                    self.giCount[gi] = 1
                else:
                    self.giCount[gi] += 1
    def convertGiToTax(self):
        print "Converting GIs to TaxIDs"
        giTaxTable = TaxDb.MySqlTable("giTax")
        count = 0 
        for gi in self.giCount:
            count += 1
            if count % 100000 == 0:
                print count
            taxId = giTaxTable.readItemFromRow("gi",gi,"taxID")
            if taxId == 0:
                taxId = "Unknown"
            if taxId in self.taxCount:
                self.taxCount[taxId] += self.giCount[gi]
            else:
                self.taxCount[taxId] = self.giCount[gi]
    def loadIntoDbTable(self):
        alignTable = TaxDb.MySqlTable("alignInfo")
        count = 0
        importData = []
        if self.fileType == "SAM":
            raise IOError("cannot import SAM file into DB yet")
        elif self.fileType == "BLAST":
            alignTable.createTable({"id"          : "INT(11) NOT NULL",
                                    "readName"    : "VARCHAR(20) NOT NULL"     ,
                                    "gi"          : "INT(11) NOT NULL",
                                    "percentId"   : "FLOAT NOT NULL"  ,
                                    "alignLength" : "INT(11) NOT NULL",
                                    "nMisMatch"   : "INT(11) NOT NULL",
                                    "nGapOpens"   : "INT(11) NOT NULL",
                                    "qStartPos"   : "INT(11) NOT NULL",
                                    "qEndPos"     : "INT(11) NOT NULL",
                                    "tStartPos"   : "INT(11) NOT NULL",
                                    "tEndPos"     : "INT(11) NOT NULL",
                                    "eValue"      : "FLOAT NOT NULL"  ,
                                    "bitScore"    : "FLOAT NOT NULL"  ,
                                    "taxID"       : "VARCHAR(20) NOT NULL"},
                                    index="taxID")
            fields = ["id","readName","gi","percentId","alignLength",
                      "nMismatch","nGapOpens","qStartPos","qEndPos",
                      "tStartPos","tEndPos","eValue","bitScore","taxID"]
            with open(self.fileName,"r") as inFile:
                giTaxTable = TaxDb.MySqlTable("giTax")
                for line in self.genLine(printProgress=True):
                    count += 1
                    data = self.blastLineExtract(line,count,giTaxTable)
                    importData.append(data)
                    if count % 40000 == 0:
                        print count
                        alignTable.addItems(fields,importData)        
                        importData = []
                giTaxTable.close()
    def blastLineExtract(self,line,count,giTaxTable):
        data = line.split("\t")
        readName    = data[0]
        gi          = int(data[1].split("|")[1])
        percentId   = float(data[2])
        alignLength = int(data[3])
        nMismatch   = int(data[4])
        nGapOpens   = int(data[5])
        qStartPos   = int(data[6])
        qEndPos     = int(data[7])
        tStartPos   = int(data[8])
        tEndPos     = int(data[9])
        eValue      = float(data[10])
        bitScore    = float(data[11].rstrip("\n"))
        taxId       = giTaxTable.readItemFromRow("gi",gi,"taxID")
        data = (count,readName,gi,percentId,alignLength,nMismatch,nGapOpens,
                qStartPos,qEndPos,tStartPos,tEndPos,eValue,bitScore,taxId)
        return data

"""
Specialized file input for blast6 output file format. Python list returns:
Specification from: http://www.drive5.com/usearch/manual/blast6out.html
0       Query label.
1       Target (database sequence or cluster centroid) label.
2       Percent identity.
3       Alignment length.
4       Number of mismatches.
5       Number of gap opens.
6       Start position in query. Query coordinates start with 1 at the 
        first base in the sequence as it appears in the input file. For
        translated searches (nucleotide queries, protein targets), query 
        start<end for +ve frame and start>end for -ve frame.
7       End position in query.
8       Start position in target. Target coordinates start with 1 at the 
        first base in sequence as it appears in the database. For 
        untranslated nucleotide searches, target start<end for plus 
        strand, start>end for a reverse-complement alignment.
9       End position in target.
10      E-value calculated using Karlin-Altschul statistics.
11      Bit score calculated using Karlin-Altschul statistics.
"""

"""
Specialized file input for SAM output file format. Python list returns:
Specification from: http://samtools.github.io/hts-specs/SAMv1.pdf
0       Query label.
1       Bitwise flag.
2       Reference sequence name.
3       1-based leftmost mapping position.
4       Mapping quality.
5       CIGAR string.
6       Ref. name of the mate/next read.
7       Position of the mate/next read.
8       Observed template length.
9       Segment sequence.
10      ASCII of Phred-scaled base quality+33
Additional entries may exist based on the options declared at the time
of alignment.
"""

def main(argv):
    inputFile = AlignmentInputFile(argv[0])
    inputFile.loadIntoDbTable()
    #inputFile.importAlignmentData()
    #inputFile.convertGiToTax()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except IndexError:
        err = "Please provide alignment filename as command line argument"
        raise IOError(err)
