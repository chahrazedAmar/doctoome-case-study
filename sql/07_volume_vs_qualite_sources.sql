-- 07_volume_vs_qualite_sources.sql
-- Pour chaque source : la QUANTITÉ (combien de questionnaires terminés)
-- ET la QUALITÉ (quel % des visiteurs terminent).
-- On isole les NOUVEAUX visiteurs, car l'objectif de Doctoome est de gagner de nouveaux utilisateurs.
SELECT
    source_clean                                                        AS source,
    COUNT(*)                                                            AS sessions,
    CAST(SUM(CASE WHEN complete THEN 1 ELSE 0 END) AS INTEGER)          AS questionnaires_termines,
    CAST(SUM(CASE WHEN complete AND NOT is_returning_visitor THEN 1 ELSE 0 END) AS INTEGER) AS termines_nouveaux,
    ROUND(100.0 * AVG(CASE WHEN complete THEN 1 ELSE 0 END), 1)         AS pct_completion,
    ROUND(100.0 * AVG(CASE WHEN NOT is_returning_visitor THEN 1 ELSE 0 END), 1) AS pct_nouveaux
FROM funnel
GROUP BY source_clean
ORDER BY termines_nouveaux DESC;