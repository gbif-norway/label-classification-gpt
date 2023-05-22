SELECT DISTINCT
  LOWER(family) AS family,
  LOWER(genus) AS genus,
  LOWER(infraspecificepithet) AS infraspecificepithet
FROM `bigquery-public-data.gbif.occurrences`
WHERE kingdom = 'Plantae';
