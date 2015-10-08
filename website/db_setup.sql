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

CREATE TABLE fileSets   (username VARCHAR(50) NOT NULL,
                     setname VARCHAR(128) NOT NULL,
                     filename VARCHAR(128) NOT NULL,
                     uniqueId INT(20) NOT NULL AUTO_INCREMENT,
                     FOREIGN KEY (username) REFERENCES users(username),
                     PRIMARY KEY (uniqueId),
                     INDEX (username,setname));
                     
CREATE DATABASE TaxAssessor_Alignments;