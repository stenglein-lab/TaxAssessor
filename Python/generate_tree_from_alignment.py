#!/usr/bin/python

import sys
import os.path
import json
import load_align_file as align
import load_tax_nodes as nodes
import load_taxID_names as tn



def getCommandLineArguments(argv):
    alignFileName = ""
    for index,entry in enumerate(argv):
        if entry == "-align":
            try:
                alignFileName = argv[index+1]
                alignFile = align.AlignmentInputFile(alignFileName)
            except IndexError:
                raise IOError("No alignment file given")
    if alignFileName == "":
        raise IOError("Please use '-align filename' to provide alignment file")
    return alignFile




def main(argv):
    alignFile = getCommandLineArguments(argv) 
    alignFile.importAlignmentData()
    alignFile.convertGiToTax()

    taxTree = nodes.TaxTree()
    taxTree.createTree(alignFile.taxCount)

    taxNames = tn.TaxIdInfo()
    taxNames.getNames() 

    taxTree.tree = taxTree.nameNodes(taxTree.tree,taxNames.taxIdToNames)

    print "Writing File"
    dj = json.dumps(taxTree.tree)
    with open("tree.json","w") as outFile:
        outFile.write(dj)

if __name__ == "__main__": 
    main(sys.argv[1:])






