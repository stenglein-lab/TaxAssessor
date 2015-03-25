#!/usr/bin/python
import json

"""
load_tax_nodes.py - 
A utility that processes taxID information into a tree utilizing taxID and parent
information from the NCBI nodes.dmp file.  Yields a dictionary ready for
export to JSON file.

Usage:

    taxTree = TaxTree()
    taxTree.createTree(taxIds)  #taxIds is a dictionary of format {taxID,count}
                                #where count is the number of GIs found from 
                                #the alignment file.  Dictionary is created by
                                #load_align_file.py
"""

class TaxTree():
    def __init__(self):
        self.fileName = ("/Users/jallison/Documents/"
                        "NCBI-dump/taxonomy/taxdmp/nodes.dmp")
        self.tree = {}
        self.children = {}
        self.parent = {"Unknown":1}
    def createTree(self,taxIds):
        """Given taxIDs in the form of a dictionary {taxID:count}, build a
        taxonomy tree from the taxID's present.
        """
        print "Importing taxonomy information"
        self.importData()
        print "Creating reduced taxonomy tree"
        taxIds = self.createChildren(taxIds)
        startNode = 1
        self.tree = self.getNodes(startNode,taxIds)
    def genData(self):
        with open(self.fileName,"r") as inFile:
            for line in inFile:
                line = line.split("|")
                taxID = int(line[0])
                parent = int(line[1])
                yield taxID,parent
    def importData(self):
        for taxID,parent in self.genData():
            self.parent[taxID] = parent
    def createChildren(self,taxIds):
        taxIdsToInclude = {}
        for taxId in taxIds:
            count = taxIds[taxId]
            taxIdsToInclude[taxId] = count
            parent = int(self.parent[taxId])
            atRoot = False
            while not atRoot:
                if parent not in taxIdsToInclude:
                    taxIdsToInclude[parent] = count
                else:
                    taxIdsToInclude[parent] += count
                if parent == 1:
                    atRoot = True
                parent = int(self.parent[parent])
        for taxId in taxIdsToInclude:
            if taxId == 1:
                continue
            parent = self.parent[taxId]
            if parent not in self.children:
                self.children[parent] = [taxId]
            else:
                self.children[parent].append(taxId)
        return taxIdsToInclude
    def getNodes(self,node,taxIds):
        tempTree = {}
        tempTree["name"] = node
        tempTree["size"] = taxIds[node]
        if node in self.children:
            children = self.children[node]
            tempTree["children"] = [self.getNodes(child,taxIds) for 
                                    child in children]
        return tempTree
    def nameNodes(self,tree,taxIdNames):
        taxId = tree["name"]
        if taxId in taxIdNames:
            tree["name"] = taxIdNames[taxId]
        else:
            tree["name"] = str(taxId)
        if "children" in tree:
            tree["children"] = [self.nameNodes(child,taxIdNames) for
                                child in tree["children"]]
        return tree


if __name__ == "__main__":
    pass
    #ncbiData = TaxTree()
    #ncbiData.createFullTree()
    #dj = json.dumps(ncbiData.tree)
    #print "Writing File"
    #with open("tree.json","w") as outFile:
    #    outFile.write(dj)



