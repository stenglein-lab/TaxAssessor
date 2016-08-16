#!/usr/bin/python
import MySQLdb
import MySQLdb.cursors as cursors

from contextlib import contextmanager





@contextmanager
def openDb(dbName):
    db = MySQLdb.connect(user='taxassessor',passwd='taxassessor',db=dbName)
    yield db
    db.close()

@contextmanager
def dbConnect():
    db = MySQLdb.connect(user='taxassessor',passwd='taxassessor')
    yield db
    db.close()

@contextmanager
def cursor(db):
    cur = db.cursor()
    yield cur
    cur.close()

@contextmanager
def openDbSS(dbName):
    db = MySQLdb.connect(user='taxassessor',passwd='taxassessor',db=dbName,
                         cursorclass=cursors.SSCursor)
    yield db
    db.close()

@contextmanager
def openDbDict(dbName):
    db = MySQLdb.connect(user='taxassessor',passwd='taxassessor',db=dbName,
                         cursorclass=cursors.DictCursor)
    yield db
    db.close()

@contextmanager
def onlyCursor(dbName):
    db = MySQLdb.connect(user='taxassessor',passwd='taxassessor',db=dbName)
    cur = db.cursor()
    yield cur
    cur.close()
    db.close()
