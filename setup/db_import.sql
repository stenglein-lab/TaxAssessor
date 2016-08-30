USE TaxAssessor_Refs;

#populate the table: seqIdToTaxId_NCBI
LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/nucl_est.accession2taxid'
INTO TABLE seqIdToTaxId_NCBI 
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES 
(accession, accessionVersion, taxId, gi);
