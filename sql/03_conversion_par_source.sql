-- 03_conversion_par_source.sql
-- Par source d'acquisition : volume, taux de démarrage et taux de complétion.
-- On ajoute la part de mobile, pour vérifier que l'écart n'est pas seulement un effet "appareil".
SELECT
    source_clean                                                  AS source,
    COUNT(*)                                                      AS sessions,
    ROUND(100.0 * AVG(CASE WHEN start    THEN 1 ELSE 0 END), 1)   AS pct_demarrage,
    ROUND(100.0 * AVG(CASE WHEN complete THEN 1 ELSE 0 END), 1)   AS pct_completion,
    ROUND(100.0 * AVG(CASE WHEN device_type = 'mobile' THEN 1 ELSE 0 END), 1) AS pct_mobile,
    -- complétion calculée seulement sur desktop : comparaison "à appareil égal"
    ROUND(100.0 * AVG(CASE WHEN complete THEN 1 ELSE 0 END)
                  FILTER (WHERE device_type = 'desktop'), 1)      AS pct_completion_desktop
FROM funnel
GROUP BY source_clean
ORDER BY pct_completion DESC;