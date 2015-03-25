#!/usr/bin/python
import mysql.connector

DNA_DB = mysql.connector.connect(user="root",database="DNA_Strings")
DNA_cursor = DNA_DB.cursor()

query_blast = ("SELECT GI, source_ID FROM blast_data "
               "WHERE Seq_ID = %(Seq_ID)s")
            
blast_Seq_ID = {"Seq_ID":"R3IYA:463:1012"}

DNA_cursor.execute(query_blast,blast_Seq_ID)

for (GI, source_ID) in DNA_cursor:
    print GI, source_ID

DNA_cursor.close()
DNA_DB.close()
