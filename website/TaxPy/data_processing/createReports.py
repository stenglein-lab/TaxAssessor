#!/usr/bin/python
import os
import json
from collections import Counter

def assessTaxIds(taxa,reads,fileName,userName):
    report = {}
    for readName in reads:
        taxId = reads[readName].assignedTaxIds[0]
        if taxId in report:
            report[taxId]["count"] += 1
        else:
            report[taxId] = {"name":taxa[taxId].name,
                             "count":1,
                             "taxId":taxId,
                             "genes":Counter()}
        seqIds = Counter(reads[readName].seqIds)
        report[taxId]["genes"] += seqIds
            
            
    report_sav = report   
    report = json.dumps(report)
    this_dir = os.path.dirname(__file__)
    with open(this_dir+"/../../uploads/"+userName+"/"+fileName+
                "_topTenTaxa.json","w") as outFile:
        outFile.write(report)
            
    new_report = []
    for taxId in report_sav:
        genes = []
        for geneId in report_sav[taxId]["genes"]:
            genes.append({"geneId":geneId,
                          "count":report_sav[taxId]["genes"][geneId]})
        report_sav[taxId]["genes"] = genes
        new_report.append(report_sav[taxId])
    
    report = json.dumps(new_report)
    with open(this_dir+"/../../uploads/"+userName+"/"+fileName+
                "_topTenTaxa1.json","w") as outFile:
        outFile.write(report)
        
        
        
                