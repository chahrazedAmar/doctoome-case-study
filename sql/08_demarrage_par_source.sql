-- 08_demarrage_par_source.sql
-- Les 35 % qui partent AVANT de commencer : qui sont-ils ?
-- On compare la source et l'appareil (et on vérifie que l'appareil ne change pas le classement).
SELECT
    source_clean                                                                    AS source,
    COUNT(*)                                                                        AS sessions,
    ROUND(100.0 * AVG(CASE WHEN NOT start THEN 1 ELSE 0 END), 1)                    AS pct_ne_commencent_pas,
    ROUND(100.0 * AVG(CASE WHEN NOT start THEN 1 ELSE 0 END)
                  FILTER (WHERE device_type = 'mobile'), 1)                         AS pct_ne_commencent_pas_mobile,
    ROUND(100.0 * AVG(CASE WHEN NOT start THEN 1 ELSE 0 END)
                  FILTER (WHERE device_type = 'desktop'), 1)                        AS pct_ne_commencent_pas_desktop,
    -- parmi ceux qui ont commencé : combien vont au bout ? (mesure de la motivation)
    ROUND(100.0 * SUM(CASE WHEN complete THEN 1 ELSE 0 END)
                / SUM(CASE WHEN start THEN 1 ELSE 0 END), 1)                        AS pct_terminent_parmi_demarres
FROM funnel
GROUP BY source_clean
ORDER BY pct_ne_commencent_pas DESC;