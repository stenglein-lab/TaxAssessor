#!/usr/bin/python
import os
import json
from collections import Counter

def assessTaxIds(taxa,reads,fileName,userName):
    print len(reads),len(taxa)
    report = {}
    for readName in reads:
        taxId = reads[readName].assignedTaxIds[0]
        if taxId in report:
            report[taxId]["count"] += 1
        else:
            report[taxId] = {"name":taxa[taxId].name,
                             "count":1,
                             "taxId":taxId,
                             "genes":{}}
        for seqId in reads[readName].seqIds:
            if seqId in report[taxId]["genes"]:
                report[taxId]["genes"][seqId] += 1
            else:
                report[taxId]["genes"][seqId] = 1

    for taxId in report:
        seqIds = []
        for seqId in report[taxId]["genes"]:
            seqIds.append({"geneId":seqId,
                          "count":report[taxId]["genes"][seqId]})
        report[taxId]["genes"] = seqIds

    report = json.dumps(report.values())

    this_dir = os.path.dirname(__file__)
    with open(this_dir+"/../../uploads/"+userName+"/"+fileName+
                "_taxonomyReport.json","w") as outFile:
        outFile.write(report)
