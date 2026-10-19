-- 13_part_nouveaux_par_mois.sql
-- La part de visiteurs "nouveaux" baisse-t-elle vraiment au fil des mois ?
-- Attention : "is_returning_visitor" ne regarde que la période fournie (juin-août 2026).
-- Tout le monde est donc "nouveau" à sa 1re visite observée : la part de revenants monte
-- mécaniquement, sans que le comportement des visiteurs ait changé (voir 14 pour la preuve).
-- On retire la période incomplète (1er-2 août).
SELECT
    strftime(started_paris, '%Y-%m')                                                AS mois,
    COUNT(*)                                                                        AS sessions,
    COUNT(*) FILTER (WHERE NOT is_returning_visitor)                                AS sessions_nouveaux,
    COUNT(*) FILTER (WHERE is_returning_visitor)                                    AS sessions_revenants,
    ROUND(100.0 * AVG(CASE WHEN is_returning_visitor THEN 0 ELSE 1 END), 1)         AS pct_nouveaux
FROM funnel
WHERE NOT flag_periode_incomplete
GROUP BY 1
ORDER BY 1;