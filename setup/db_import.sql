USE TaxAssessor_Refs;

#populate the table: seqIdToTaxId_NCBI
LOAD DATA INFILE ‘database_import/nucl_est.accession2taxid’
INTO TABLE seqIdToTaxId_NCBI
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
(accession, accessionVersion, taxId, gi)
IGNORE 1 LINES;
