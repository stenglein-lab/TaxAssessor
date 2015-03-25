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
        with open(self.fileName,"r") as inFile:
            line = inFile.readline()
        tabLine = line.split("\t")
        try:
            if "|" in tabLine[1]:
                fileType = "BLAST"
            elif "|" in tabLine[2]:
                fileType = "SAM"
            else:
                raise IOError(err+"\nUnable to determine filetype from line.")
        except IndexError:
            raise IOError(err+"\nCould not parse first line.")
        return fileType
    def importAlignmentData(self):
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
    inputFile.importAlignmentData()
    inputFile.convertGiToTax()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except IndexError:
        err = "Please provide alignment filename as command line argument"
        raise IOError(err)
