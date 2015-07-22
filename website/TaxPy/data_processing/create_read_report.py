#!/usr/bin/python

import json

class ReadReport():
    def __init__(self,readMinGis,readMinScore,
                      readMinCount,taxCount,gis):
        self.readMinGis   = readMinGis
        self.readMinScore = readMinScore
        self.readMinCount = readMinCount
        self.taxCount     = taxCount
        self.gis          = gis
        
    def createReport(self):
        report = {}
        report['nReads']    = len(self.readMinGis.keys())
        report['nAligns']   = sum(self.readMinCount.values())
        report['aveAligns'] = report['nAligns']/report['nReads']
        report['minAligns'] = min(self.readMinCount.values())
        report['maxAligns'] = max(self.readMinCount.values())
        report['nGis']      = len(self.gis)
        report['nTaxIds']   = len(self.taxCount.values())

        report = json.dumps(report)
        return report

