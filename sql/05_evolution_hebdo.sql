-- 05_evolution_hebdo.sql
-- Évolution par semaine (heure de Paris). On retire la période incomplète (1er-2 août).
-- On sépare NOUVEAUX et REVENANTS : "is_returning_visitor" ne regarde que la période fournie,
-- donc la part de revenants monte mécaniquement (0 % la 1re semaine) et peut créer une fausse tendance.
SELECT
    CAST(semaine AS DATE)                                                          AS semaine_du,
    COUNT(*)                                                                       AS sessions,
    COUNT(*) FILTER (WHERE NOT is_returning_visitor)                               AS sessions_nouveaux,
    COUNT(*) FILTER (WHERE is_returning_visitor)                                   AS sessions_revenants,
    ROUND(100.0 * AVG(CASE WHEN complete THEN 1 ELSE 0 END), 1)                    AS pct_completion,
    ROUND(100.0 * AVG(CASE WHEN complete THEN 1 ELSE 0 END)
                  FILTER (WHERE NOT is_returning_visitor), 1)                      AS pct_completion_nouveaux,
    ROUND(100.0 * AVG(CASE WHEN device_type = 'mobile' THEN 1 ELSE 0 END), 1)      AS pct_mobile
FROM funnel
WHERE NOT flag_periode_incomplete
GROUP BY semaine
ORDER BY semaine;