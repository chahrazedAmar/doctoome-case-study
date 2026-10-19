-- 09_sources_a_age_egal.sql
-- Les assistants IA amènent un public plus jeune. Pour comparer les sources sans cet effet d'âge
-- (variable de confusion), on calcule la complétion et le "risque potentiel" DANS chaque tranche d'âge.
-- On exclut les âges inconnus, les mineurs et les années suspectes (1946, 2008).
WITH base AS (
    SELECT
        f.session_id, f.source_clean, f.complete,
        CASE WHEN f.age BETWEEN 18 AND 34 THEN '18-34'
             WHEN f.age BETWEEN 35 AND 49 THEN '35-49'
             WHEN f.age BETWEEN 50 AND 64 THEN '50-64'
             ELSE '65+' END                                AS tranche_age,
        o.outcome_category
    FROM funnel f
    LEFT JOIN outcomes o ON o.session_id = f.session_id      -- LEFT JOIN : on garde aussi les non-terminés
    WHERE f.age IS NOT NULL AND NOT f.flag_mineur AND NOT f.flag_annee_suspecte
      AND f.source_clean IN ('ai_assistant', 'google_organic', 'google_ads')
)
SELECT
    source_clean                                                        AS source,
    tranche_age,
    COUNT(*)                                                            AS sessions,
    ROUND(100.0 * AVG(CASE WHEN complete THEN 1 ELSE 0 END), 1)         AS pct_completion,
    -- risque potentiel : calculé seulement parmi les questionnaires terminés
    ROUND(100.0 * AVG(CASE WHEN outcome_category = 'possible_risk' THEN 1 ELSE 0 END)
                  FILTER (WHERE complete), 1)                           AS pct_risque_potentiel
FROM base
GROUP BY source_clean, tranche_age
ORDER BY tranche_age, source_clean;