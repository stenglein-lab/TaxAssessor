#!/usr/bin/python
import os
import subprocess
import time

class webServerInstance():
    def __init__(self,port,currentDir):
        self.port       = port
        self.currentDir = currentDir
        self.process    = None
        
    def startProcess(self):
        cmd = [self.currentDir+"/tax_assessor.py","--port="+str(self.port)]
        self.process = subprocess.Popen(cmd,universal_newlines=True)

    def terminateProcess(self):
        self.process.terminate()




if __name__ == "__main__":

    ports      = [8000,8001,8002,8003]
    webServers = []
    currentDir = os.path.dirname(os.path.realpath(__file__))
    
    for port in ports:
        webServer = webServerInstance(port,currentDir)
        webServer.startProcess()
        webServers.append(webServer)
    
    while True:
        cmd = raw_input()
        if cmd.lower() == "exit":
            for webServer in webServers:
                webServer.terminateProcess()
            break
                
                
                
                
                