CREATE DATABASE TaxAssessor;

USE TaxAssessor;

CREATE TABLE users  (username VARCHAR(50) NOT NULL PRIMARY KEY,
                     password VARCHAR(50) NOT NULL,
                     firstName VARCHAR(50) NOT NULL,
                     lastName VARCHAR(50) NOT NULL);
