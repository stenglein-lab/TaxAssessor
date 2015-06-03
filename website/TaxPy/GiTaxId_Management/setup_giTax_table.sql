CREATE DATABASE TaxAssessor_Refs;

USE TaxAssessor_Refs;

CREATE TABLE GiTax_NCBI (gi INT(20) NOT NULL,
                         taxID INT(20) NOT NULL,
                         PRIMARY KEY (gi));

CREATE TABLE TaxNames_NCBI (taxID INT(20) NOT NULL,
                            name VARCHAR(120) NOT NULL,
                            PRIMARY KEY (taxID));
