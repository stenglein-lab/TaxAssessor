USE TaxAssessor_Refs;
/*
#populate the table: seqIdToTaxId_NCBI
LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/nucl_est.accession2taxid' 
INTO TABLE seqIdToTaxId_NCBI 
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES 
(accession, accessionVersion, taxId, gi);

LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/nucl_gb.accession2taxid' 
INTO TABLE seqIdToTaxId_NCBI 
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES 
(accession, accessionVersion, taxId, gi);

LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/nucl_gss.accession2taxid' 
INTO TABLE seqIdToTaxId_NCBI 
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES 
(accession, accessionVersion, taxId, gi);

LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/nucl_wgs.accession2taxid' 
INTO TABLE seqIdToTaxId_NCBI 
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES 
(accession, accessionVersion, taxId, gi);

LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/prot.accession2taxid' 
INTO TABLE seqIdToTaxId_NCBI 
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES 
(accession, accessionVersion, taxId, gi);
*/
#populate the table: taxIdNodes_NCBI
LOAD DATA INFILE '/home/jallison/TaxAssessor/setup/database_import/nodes.dmp' 
INTO TABLE taxIdNodes_NCBI 
FIELDS TERMINATED BY '\t|\t' 
LINES TERMINATED BY '\r\n' 
IGNORE 1 LINES 
(child, parent);