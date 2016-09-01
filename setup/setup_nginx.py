#!/usr/bin/python
import os

if __name__ == "__main__":
    taxAssDir = os.environ['TaxAssessor']
    serverName = raw_input("Server name: ")
    listenPort = raw_input("Listen port: ")
    with open("../nginx/conf/new.conf","w") as outFile:
        with open("../nginx/conf/setup_nginx.conf","r") as inFile:
            for line in inFile:
                if "{TaxAssessor}" in line:
                    outFile.write(line.replace('{TaxAssessor}',taxAssDir))
                elif "{listen_port}" in line:
                    outFile.write(line.replace('{listen_port}',listenPort))
                elif "{server_name}" in line:
                    outFile.write(line.replace('{server_name}',serverName))
                else:
                    outFile.write(line)
                
            
                
                
    os.rename("../nginx/conf/nginx.conf","../nginx/conf/nginx_save.conf")
    os.rename("../nginx/conf/new.conf","../nginx/conf/nginx.conf")
    