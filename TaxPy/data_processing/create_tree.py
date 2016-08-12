#!/usr/bin/python
from collections import OrderedDict

class Tree():
    def __init__(self,taxa):
        self.taxa = taxa
    def buildTree(self,taxId):
        tempTree = OrderedDict({"name":self.taxa[taxId].name,
                                "taxId":taxId,
                                "size":self.taxa[taxId].count,
                                "score":self.taxa[taxId].aveScore})
        if len(self.taxa[taxId].children) > 0:
            children = self.taxa[taxId].children
            tempTree["children"] = [self.buildTree(child) for 
                                    child in children]
        return tempTree