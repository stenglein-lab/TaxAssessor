#!/usr/bin/python

import mysql.connector

DNA_DB = mysql.connector.connect(user="root",database="DNA_Strings")
DNA_cursor = DNA_DB.cursor()

add_blast = ("INSERT INTO blast_data "
            "(Seq_ID, GI, source_ID) "
            "VALUES (%s, %s, %s)")
            
blast_entry = ("R3IYA:463:1012","281177210","AP009378.1")

DNA_cursor.execute(add_blast,blast_entry)
DNA_id = DNA_cursor.lastrowid


DNA_DB.commit()
DNA_cursor.close()
DNA_DB.close()
