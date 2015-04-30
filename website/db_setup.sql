CREATE DATABASE TaxAssessor;

USE TaxAssessor;

CREATE TABLE users  (username VARCHAR(50) NOT NULL PRIMARY KEY,
                     password VARCHAR(128) NOT NULL,
                     firstName VARCHAR(50) NOT NULL,
                     lastName VARCHAR(50) NOT NULL,
                     salt VARCHAR(32) NOT NULL);


CREATE TABLE files  (username VARCHAR(50) NOT NULL,
                     filename VARCHAR(128) NOT NULL,
                     dateModified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                     FOREIGN KEY (username) REFERENCES users(username),
                     PRIMARY KEY (username,filename));
