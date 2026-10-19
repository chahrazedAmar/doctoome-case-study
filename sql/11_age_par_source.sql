-- 11_age_par_source.sql
-- Répartition par tranche d'âge de chaque source : les assistants IA amènent-ils un public plus jeune ?
-- Âge DÉCLARÉ ; on exclut les âges inconnus, les mineurs et les années suspectes (1946, 2008).
WITH base AS (
    SELECT
        source_clean,
        age,
        CASE WHEN age BETWEEN 18 AND 34 THEN '18-34'
             WHEN age BETWEEN 35 AND 49 THEN '35-49'
             WHEN age BETWEEN 50 AND 64 THEN '50-64'
             ELSE '65+' END AS tranche_age
    FROM funnel
    WHERE age IS NOT NULL AND NOT flag_mineur AND NOT flag_annee_suspecte
      AND source_clean <> 'other'                      -- "other" : trop hétérogène pour être interprété
)
SELECT
    source_clean                                                          AS source,
    COUNT(*)                                                              AS sessions,
    CAST(MEDIAN(age) AS INTEGER)                                          AS age_median,
    -- pour chaque tranche : % des sessions de cette source
    ROUND(100.0 * AVG(CASE WHEN tranche_age = '18-34' THEN 1 ELSE 0 END), 1) AS pct_18_34,
    ROUND(100.0 * AVG(CASE WHEN tranche_age = '35-49' THEN 1 ELSE 0 END), 1) AS pct_35_49,
    ROUND(100.0 * AVG(CASE WHEN tranche_age = '50-64' THEN 1 ELSE 0 END), 1) AS pct_50_64,
    ROUND(100.0 * AVG(CASE WHEN tranche_age = '65+'   THEN 1 ELSE 0 END), 1) AS pct_65_plus
FROM base
GROUP BY source_clean
ORDER BY age_median;