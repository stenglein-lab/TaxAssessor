USE TaxAssessor_Refs;

CREATE TABLE taxIdNodes_NCBI (child INT(11) NOT NULL,
                              parent INT(11) NOT NULL,
                              PRIMARY KEY (child),
                              INDEX (parent));