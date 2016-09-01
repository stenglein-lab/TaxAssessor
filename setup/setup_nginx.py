#!/usr/bin/python
import os









if __name__ == "__main__":
    taxAssDir = os.environ['TaxAssessor']
    with open("../nginx/conf/new.conf","w") as outFile:
        with open("../nginx/conf/nginx.conf","r") as inFile:
            for line in inFile:
                outFile.write(line.replace('{TaxAssessor}',taxAssDir))
    os.rename("../nginx/conf/nginx.conf","../nginx/conf/setup_nginx.conf")
    os.rename("../nginx/conf/new.conf","../nginx/conf/nginx.conf")
    

