#!/usr/bin/python

class InputFile():
    def __init__(self,fileName):
        self.fileName = fileName
    def genLine(self):
        with open(self.fileName,"r") as inFile:
            for line in inFile:
                yield line

class GeneFile(InputFile):
    def __init__(self,fileName):
        self.fileName = fileName
        self.genes = {}
    def checkGeneIds(self,geneMap):
        for line in self.genLine():
            line = line.split("\t")
            geneId = line[0].split("|")[0]
            abundance = line[1].strip("\n")
            if geneId in geneMap:
                geneName = geneMap[geneId]    
                if geneName not in self.genes:
                    self.genes[geneName] = [[geneId,abundance]]
                else:
                    self.genes[geneName].append([geneId,abundance])
    def writeGenesToFile(self,outFileName):
        with open(outFileName,"w") as outFile:
            for geneName in self.genes:
                outFile.write(geneName+"\n")
                for entries in self.genes[geneName]:
                    for entry in entries:
                        outFile.write("\t"+entry)
                    outFile.write("\n")
                outFile.write("\n")
        

class MapFile(InputFile):
    def __init__(self,fileName):
        self.fileName = fileName
        self.geneMap = {}
    def fillGeneMap(self,geneList):
        for line in self.genLine():
            line = line.split("\t")
            geneId = line[0]
            geneName = line[1].rstrip("\n").lower()
            for gene in geneList:
                if gene in geneName:
                    self.geneMap[geneId] = geneName
            





if __name__ == "__main__":

    geneList = ["amylase",
                "protease",
                "phosphatase",
                "cellulase",
                "lipase",
                "glucanase",
                "glucosidase",
                "cellobiohydrolase",
                "phosphorylase",
                "xylanase",
                "hydrolase",
                "hydrogenase",
                "formyltetrahydrofolate synthetase",
                "methyl com reductase",
                "formate dehydrogenase",
                "coa transferase"]

    geneFamily1 = GeneFile("1_trimQ17_filter35.full_genefamilies.tsv")
    geneFamily2 = GeneFile("2_trimQ17_filter35.full_genefamilies.tsv")
    geneMap     = MapFile("map_uniref50_name.txt")

    print "filling gene map"
    geneMap.fillGeneMap(geneList)
    
    print "checking file 1"
    geneFamily1.checkGeneIds(geneMap.geneMap)

    print "writing file 1"
    geneFamily1.writeGenesToFile("1_genes.txt")

    print "checking file 2"
    geneFamily2.checkGeneIds(geneMap.geneMap)

    print "writing file 2"
    geneFamily2.writeGenesToFile("2_genes.txt")

