#!/usr/bin/python
import os









if __name__ == "__main__":
    taxAssDir = os.environ['TaxAssessor']
    with open("../nginx/conf/new.conf","w") as outFile:
        with open("../nginx/conf/nginx.conf","r") as inFile:
            for line in inFile:
                fout.write(line.replace('{TaxAssessor}',taxAssDir))



