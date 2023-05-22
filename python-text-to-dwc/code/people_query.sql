WITH unnested AS (
  SELECT 
    LOWER(TRIM(person_name)) AS person_name,
    countrycode
  FROM 
    `bigquery-public-data.gbif.occurrences`,
    UNNEST(recordedby.array) AS recordedby,
    UNNEST(SPLIT(REPLACE(recordedby.array_element, '&', ';'), ';')) AS person_name
  WHERE 
    recordedby IS NOT NULL
    AND basisofrecord = 'PRESERVED_SPECIMEN'
    AND kingdom = 'Plantae'

  UNION ALL

  SELECT 
    LOWER(TRIM(person_name)) AS person_name,
    countrycode
  FROM 
    `bigquery-public-data.gbif.occurrences`,
    UNNEST(identifiedby.array) AS identifiedby,
    UNNEST(SPLIT(REPLACE(identifiedby.array_element, '&', ';'), ';')) AS person_name
  WHERE 
    identifiedby IS NOT NULL
    AND basisofrecord = 'PRESERVED_SPECIMEN'
    AND kingdom = 'Plantae'
)
SELECT 
  person_name,
  countrycode,
  COUNT(*) AS person_count
FROM 
  unnested
GROUP BY
  person_name, countrycode
HAVING
  person_count > 3
ORDER BY
  person_count DESC;