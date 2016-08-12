#!/usr/bin/python

import json
import math

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
        bins,binCounts = self.binGiCounts()
        report['giBins'] = bins
        report['giBinCounts'] = binCounts

        report = json.dumps(report)
        return report
        
    def binGiCounts(self):
        maxBin = max(len(data) for data in self.readMinGis.values())
        bins = []
        binCounts = []
        if maxBin == 1:
            bins = [0,1,2]
            binCounts = [0,0,0]
        else:
            binRes = 20
            for i in xrange(binRes+1):
                scale = i/float(binRes)
                bin = math.ceil(scale * maxBin)
                if bin == 0:
                    bin += 1
                bins.append(bin)
                binCounts.append(0)

            diff = bins[1]
                
            for read in self.readMinGis:
                giCount = len(self.readMinGis[read])
                for index, value in enumerate(bins):
                    if (giCount > value-diff and giCount <= value+diff):
                        binCounts[index] += 1
                        break
                      
        return (bins,binCounts)