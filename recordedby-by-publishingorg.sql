SELECT
  publishingOrgKey,
  /* Publisher name provided by GBIF occurrence column */
  publisher AS publisherName,
  CONCAT('https://www.gbif.org/publisher/', publishingOrgKey) AS publisherUrl,
  COUNT(*) AS total_records,
  SUM(CASE WHEN recordedByID IS NOT NULL THEN 1 ELSE 0 END) AS records_with_recordedByID,
  100.0 * SUM(CASE WHEN recordedByID IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS pct_with_recordedByID,
  SUM(CASE WHEN (
      GBIF_StringArrayLike(recordedByID, 'https://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.linkedin.com/profile/view?id=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.linkedin.com/profile/view?id=*', FALSE)
    ) THEN 1 ELSE 0 END) AS records_with_valid_recordedByID,
  100.0 * SUM(CASE WHEN (
      GBIF_StringArrayLike(recordedByID, 'https://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.linkedin.com/profile/view?id=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.linkedin.com/profile/view?id=*', FALSE)
    ) THEN 1 ELSE 0 END) / COUNT(*) AS pct_valid_recordedByID,
  SUM(CASE WHEN recordedByID IS NOT NULL AND NOT (
      GBIF_StringArrayLike(recordedByID, 'https://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.linkedin.com/profile/view?id=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.linkedin.com/profile/view?id=*', FALSE)
    ) THEN 1 ELSE 0 END) AS records_with_invalid_recordedByID,
  100.0 * SUM(CASE WHEN recordedByID IS NOT NULL AND NOT (
      GBIF_StringArrayLike(recordedByID, 'https://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://orcid.org/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://scholar.google.com/citations?user=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.researcherid.com/rid/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.wikidata.org/entity/*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'https://www.linkedin.com/profile/view?id=*', FALSE) OR
      GBIF_StringArrayLike(recordedByID, 'http://www.linkedin.com/profile/view?id=*', FALSE)
    ) THEN 1 ELSE 0 END) / COUNT(*) AS pct_invalid_recordedByID,
  SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://orcid.org/*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://orcid.org/*', FALSE) THEN 1 ELSE 0 END) AS records_with_orcid,
  100.0 * SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://orcid.org/*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://orcid.org/*', FALSE) THEN 1 ELSE 0 END) / COUNT(*) AS pct_with_orcid,
  SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://scholar.google.com/citations?user=*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://scholar.google.com/citations?user=*', FALSE) THEN 1 ELSE 0 END) AS records_with_google_scholar,
  100.0 * SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://scholar.google.com/citations?user=*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://scholar.google.com/citations?user=*', FALSE) THEN 1 ELSE 0 END) / COUNT(*) AS pct_with_google_scholar,
  SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://www.researcherid.com/rid/*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://www.researcherid.com/rid/*', FALSE) THEN 1 ELSE 0 END) AS records_with_researcherid,
  100.0 * SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://www.researcherid.com/rid/*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://www.researcherid.com/rid/*', FALSE) THEN 1 ELSE 0 END) / COUNT(*) AS pct_with_researcherid,
  SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://www.wikidata.org/entity/*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://www.wikidata.org/entity/*', FALSE) THEN 1 ELSE 0 END) AS records_with_wikidata,
  100.0 * SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://www.wikidata.org/entity/*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://www.wikidata.org/entity/*', FALSE) THEN 1 ELSE 0 END) / COUNT(*) AS pct_with_wikidata,
  SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://www.linkedin.com/profile/view?id=*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://www.linkedin.com/profile/view?id=*', FALSE) THEN 1 ELSE 0 END) AS records_with_linkedin,
  100.0 * SUM(CASE WHEN GBIF_StringArrayLike(recordedByID, 'https://www.linkedin.com/profile/view?id=*', FALSE) OR GBIF_StringArrayLike(recordedByID, 'http://www.linkedin.com/profile/view?id=*', FALSE) THEN 1 ELSE 0 END) / COUNT(*) AS pct_with_linkedin
FROM occurrence
WHERE publishingOrgKey IS NOT NULL
GROUP BY publishingOrgKey, publisher
ORDER BY pct_with_recordedByID DESC;

