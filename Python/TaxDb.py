#!/usr/bin/python

import mysql.connector as mc

"""
TaxDb.py - 

Basic CRUD wrapper for the MySQL db 'TaxAssessor'.  Requires a name 
(string) and row declarations.

Example usages:

Instantiate: myTable = MySqlTable("tableName") #can update/read from
                                               #existing table

Create Table: --WARNING WILL DROP EXISTING TABLE OF SAME NAME--
              myTable.createTable({"row1":"int(11) NOT NULL",
                                   "row2":"VARCHAR(5) NOT NULL"},
                                   index="row1") 

Read Entries: myTable.readRow("row1",52) #returns whole row
              myTable.readItemFromRow("row1",52,"row2") #returns "row2" value

Update (Add) Table: myTable.addItems(["row1","row2"],[(52,"hi"),(32,"stuff")])
Delete entries: NYI 
"""

class MySqlTable():
    def __init__(self,name):
        self.name = name
        self.database = mc.connect(user='root',database="TaxAssessor")
        self.cursor = self.database.cursor()
    def __del__(self):
        self.cursor.close()
        self.database.close()
    def close(self):
        self.cursor.close()
        self.database.close()
    def tableExists(self): 
        command = ("SELECT COUNT(*) FROM information_schema.tables "
                   "WHERE table_name = '"+self.name)+"'"
        self.cursor.execute(command)
        if self.cursor.fetchone()[0] == 1:
            status = True
        else:
            status = False
        return status
    def createTable(self,fields,primaryKey=None,index=None):
        if self.tableExists():
            print "Table: '"+self.name+"' already exists, reinitializing table"
            self.dropTable()
        else:
            print "Table: '"+self.name+"' does not exist, creating new table"
        print "Creating Table: "+self.name
        command =  "CREATE TABLE "+self.name+" ("
        for name in fields:
            nextcmd = " "+name+" "+fields[name]+","
            command += nextcmd
        if primaryKey != None:
            nextcmd = " PRIMARY KEY("+primaryKey+")"
            command = command.rstrip(")")+","+nextcmd
        command = command.rstrip(",") + " )"
        if index != None:
            nextcmd = " INDEX("+index+") )"
            command = command.rstrip(")")+","+nextcmd
        self.cursor.execute(command)
        return
    def dropTable(self):
        print "Dropping table: "+self.name
        command = "DROP TABLE "+self.name
        self.cursor.execute(command)
        return
    def addItems(self,fields,data,unique=False):
        """Add an item or items into the table.  Requires an array of the
        fields to be added, an array of tuples of the values to be added
        """
        command = "INSERT INTO "+self.name+" ("
        for item in fields:
            command += item+","
        command = command.rstrip(",")+") VALUES "

        data = str(data)
        data = data.lstrip("[").rstrip("]")
        command += data
        self.cursor.execute(command)
        self.database.commit()
    def readRow(self,columnName,searchItem):
        command = ("SELECT * FROM "+self.name+
                   " WHERE "+columnName+"='"+str(searchItem)+"'")
        self.cursor.execute(command)
        data = self.cursor.fetchall()
        return data
    def readItemFromRow(self,columnName,searchItem,returnItem):
        command = ("SELECT "+returnItem+" FROM "+self.name+
                   " WHERE "+columnName+"='"+str(searchItem)+"'")
        self.cursor.execute(command)
        data = self.cursor.fetchone()
        if data == None:
            return "Unknown"
        else:
            return data[0]


def main():
    mySqlTable = MySqlTable("test")
    mySqlTable.createTable({"gi":"int(11) NOT NULL","taxID":"int(11) NOT NULL"},index="gi")
    mySqlTable.addItems(["gi","taxID"],(123,456))
    print mySqlTable.readRow("gi",123)
    print mySqlTable.readItemFromRow("gi",123,"taxID")
    mySqlTable.dropTable()

if __name__ == "__main__":
    main()

