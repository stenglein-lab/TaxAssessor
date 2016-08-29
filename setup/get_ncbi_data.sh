wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/gi_taxid_nucl.dmp.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/gi_taxid_prot.dmp.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_est.accession2taxid.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gss.accession2taxid.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/prot.accession2taxid.gz
wget -P database_import ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
gunzip database_import/*.gz
tar -xvf database_import/taxdump.tar
