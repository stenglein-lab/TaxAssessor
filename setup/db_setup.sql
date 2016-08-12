CREATE DATABASE TaxAssessor_Users;

USE TaxAssessor_Users;

CREATE TABLE users  (username VARCHAR(50) NOT NULL PRIMARY KEY,
                     password VARCHAR(128) NOT NULL,
                     firstName VARCHAR(50) NOT NULL,
                     lastName VARCHAR(50) NOT NULL,
                     salt VARCHAR(32) NOT NULL,
                     currentFile VARCHAR(128),
                     INDEX (username));


CREATE TABLE files  (username VARCHAR(50) NOT NULL,
                     filename VARCHAR(128) NOT NULL,
                     dateModified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                     status VARCHAR(50) NOT NULL DEFAULT "None",
                     uniqueId INT(20) NOT NULL AUTO_INCREMENT,
                     FOREIGN KEY (username) REFERENCES users(username),
                     PRIMARY KEY (uniqueId),
                     INDEX (username,filename));

CREATE TABLE fileOptions (uniqueId INT(20) NOT NULL,
                          fileFormat VARCHAR(20) NOT NULL,
                          readNameIndex INT(10) NOT NULL,
                          delimiter VARCHAR(20) NOT NULL,
                          seqIdIndex INT(10) NOT NULL,
                          scoreIndex FLOAT(20) NOT NULL,
                          scorePreference VARCHAR(20) NOT NULL,
                          header VARCHAR(128) NOT NULL,
                          seqIdDelimiter VARCHAR(20) DEFAULT NULL,
                          seqIdSubIndex INT(10) DEFAULT NULL,
                          refStartPosIndex INT(20) DEFAULT NULL,
                          refEndPosIndex INT(20) DEFAULT NULL,
                          seqLength INT(20) DEFAULT NULL,
                          cigarIndex INT(2) DEFAULT NULL,
                          FOREIGN KEY (uniqueId) REFERENCES files(uniqueId),
                          PRIMARY KEY (uniqueId));


CREATE TABLE fileSets   (username VARCHAR(50) NOT NULL,
                         setname VARCHAR(128) NOT NULL,
                         filename VARCHAR(128) NOT NULL,
                         uniqueId INT(20) NOT NULL AUTO_INCREMENT,
                         FOREIGN KEY (username) REFERENCES users(username),
                         PRIMARY KEY (uniqueId),
                         INDEX (username,setname));

CREATE DATABASE TaxAssessor_Alignments;
