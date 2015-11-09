import json
import os
import warnings
from copy import deepcopy as dc
from scipy import stats
import numpy
from collections import OrderedDict


class TaxTreeSample():
    def __init__(self,fileName,userName):
        self.fileName = fileName
        this_dir = os.path.dirname(__file__)
        self.treeFile = (this_dir+"/../../uploads/"+userName+"/"+
                         fileName+"_tree.json")
        self.flatTree = {}
        self.tree = None
    def flattenTree(self):
        def flatten(self,tree):
            taxId = tree["taxId"]
            #if tree["size"] < 5:
            #    return
            self.flatTree[taxId] = {"size"    :tree["size"],
                                    "name"    :tree["name"],
                                    "children":set()}
            try:
                for child in tree["children"]:
                    if child["size"] < 5:
                        pass
                    else:
                        self.flatTree[taxId]["children"].add(child["taxId"])
                        flatten(self,child)
            except KeyError:
                return  
        def normalizeFlatTreeSizes(self):
            totalSize = float(self.flatTree[1]["size"])
            for taxId in self.flatTree:
                self.flatTree[taxId]["size"]=self.flatTree[taxId]["size"]/totalSize
        with open(self.treeFile,"r") as inFile:
            self.tree = json.loads(inFile.read())
        flatten(self,self.tree)
        normalizeFlatTreeSizes(self)



class TaxTreeSet():
    def __init__(self):
        self.samples = []
        self.combinedFlatTree = {}
        self.nSamples = 0
    def addSample(self,sample):
        self.samples.append(sample)
        self.nSamples = len(self.samples)
    def combineTrees(self):
        for sample in self.samples:
            for taxId in sample.flatTree:
                if taxId in self.combinedFlatTree:
                    self.combinedFlatTree[taxId]["size"].append(
                                sample.flatTree[taxId]["size"])
                else:
                    self.combinedFlatTree[taxId] = \
                            {"size"    :[sample.flatTree[taxId]["size"]],
                             "name"    :sample.flatTree[taxId]["name"],
                             "children":set()}
                for child in sample.flatTree[taxId]["children"]:
                    self.combinedFlatTree[taxId]["children"].add(child)
        self.addZeros()
    def addZeros(self):
        for taxId in self.combinedFlatTree:
            nSizes = len(self.combinedFlatTree[taxId]["size"])
            if nSizes < self.nSamples:
                for i in xrange(self.nSamples-nSizes):
                    self.combinedFlatTree[taxId]["size"].append(0)        
        
class FinalTree():
    def __init__(self,flatTree1,flatTree2):
        self.flatTree1 = flatTree1
        self.flatTree2 = flatTree2 
        self.fullFlatTree = {}
        self.fullTree = {}
        self.stats  = None
    def combineTrees(self):
        for flatTree in [self.flatTree1,self.flatTree2]:
            for taxId in flatTree:
                if taxId not in self.fullFlatTree:
                    self.fullFlatTree[taxId] = {"name":flatTree[taxId]["name"],
                                                "children":set(),
                                                "size":-1}
                for child in flatTree[taxId]["children"]:
                    self.fullFlatTree[taxId]["children"].add(child)
    def reformTreeTTest(self,parentTaxId=1):
        tree = OrderedDict({"name"    :self.fullFlatTree[parentTaxId]["name"],
                            "taxId"   :parentTaxId,
                            "size"    :self.fullFlatTree[parentTaxId]["size"],
                            "children":[]})
        for childTaxId in self.fullFlatTree[parentTaxId]["children"]:
            tree["children"].append(self.reformTreeTTest(childTaxId))
        return tree
    def reformTreeZScore(self,parentTaxId=1):
        tree = OrderedDict({"name"    :self.fullFlatTree[parentTaxId]["name"],
                            "taxId"   :parentTaxId,
                            "zscores" :self.fullFlatTree[parentTaxId]["zscores"],
                            "size"    :self.fullFlatTree[parentTaxId]["size"]})

        if len(self.fullFlatTree[parentTaxId]["children"]) > 0:
            tree["children"] = [self.reformTreeZScore(childTaxId) for 
                    childTaxId in self.fullFlatTree[parentTaxId]["children"]]
            
        #for childTaxId in self.fullFlatTree[parentTaxId]["children"]:
        #    tree["children"].append(self.reformTreeZScore(childTaxId))
        return tree    

def compareData(set1,set2,userName):

    

    #Setup Objects
    set1Data = TaxTreeSet()
    for fileName in set1:
        set1Data.addSample(TaxTreeSample(fileName,userName))
    set2Data = TaxTreeSet()
    for fileName in set2:
        set2Data.addSample(TaxTreeSample(fileName,userName))

    #Flatten & combine the trees for each set
    for treeData in set1Data.samples:
        treeData.flattenTree()
    set1Data.combineTrees()
    for treeData in set2Data.samples:
        treeData.flattenTree()
    set2Data.combineTrees()
    
    finalFlatTree = FinalTree(set1Data.combinedFlatTree,
                                set2Data.combinedFlatTree)
    finalFlatTree.combineTrees()
    
    #Perform stats
    if (set1Data.nSamples > 3) and (set2Data.nSamples > 3): #t-test
        for taxId in finalFlatTree.fullFlatTree:
            if taxId not in set1Data.combinedFlatTree:
                set1Sizes = [0]*set1Data.nSamples
            else:
                set1Sizes = set1Data.combinedFlatTree[taxId]["size"]
            if taxId not in set2Data.combinedFlatTree:
                set2Sizes = [0]*set2Data.nSamples
            else:
                set2Sizes = set2Data.combinedFlatTree[taxId]["size"]
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                results = stats.ttest_ind(set1Sizes,set2Sizes,equal_var=False)

            finalFlatTree.fullFlatTree[taxId]["size"] = results[1]
        finalFlatTree.fullTree = finalFlatTree.reformTreeTTest()
    elif (set1Data.nSamples > 3) or (set2Data.nSamples > 3): #z-score
        if set1Data.nSamples > 0:
            setData = set1Data
        elif set2Data.nSamples > 0:
            setData = set2Data
        for taxId in finalFlatTree.fullFlatTree:            
            setSizes = setData.combinedFlatTree[taxId]["size"]
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                try:
                    results = stats.zscore(setSizes)
                except RuntimeWarning:
                    results = [0]*setData.nSamples
            finalFlatTree.fullFlatTree[taxId]["zscores"] = {}
            for index,result in enumerate(results):
                finalFlatTree.fullFlatTree[taxId]["zscores"][setData.samples[index].fileName] = results[index]
            finalFlatTree.fullFlatTree[taxId]["size"] = max(results)
        finalFlatTree.fullTree = finalFlatTree.reformTreeZScore()
    return json.dumps(finalFlatTree.fullTree,sort_keys=False)








