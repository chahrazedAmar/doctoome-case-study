-- 14_controles_suivi.sql
-- Contrôles de fiabilité du suivi (tracking). Chaque ligne : combien de cas, sur combien.
WITH premiere AS (
    -- date de la 1re session observée de chaque visiteur
    SELECT visitor_id, MIN(started_paris) AS premiere_session
    FROM funnel
    GROUP BY visitor_id
)
SELECT
    'visiteurs dont first_seen_at = 1re session observée (aucun historique avant juin)' AS controle,
    CAST(SUM(CASE WHEN v.first_seen_at = p.premiere_session THEN 1 ELSE 0 END) AS INTEGER) AS cas,
    CAST(COUNT(*) AS INTEGER)                                                              AS sur
FROM premiere p
JOIN visitors v ON v.visitor_id = p.visitor_id
UNION ALL
SELECT
    'sessions avec "questionnaire_start" mais sans affichage de la Q1 ni aucune réponse',
    CAST(SUM(CASE WHEN start AND NOT vue_q1 THEN 1 ELSE 0 END) AS INTEGER),
    CAST(SUM(CASE WHEN start THEN 1 ELSE 0 END) AS INTEGER)
FROM funnel
UNION ALL
SELECT
    'sessions avec les 5 réponses mais sans résultat enregistré',
    CAST(SUM(CASE WHEN flag_5rep_sans_resultat THEN 1 ELSE 0 END) AS INTEGER),
    CAST(COUNT(*) AS INTEGER)
FROM funnel
UNION ALL
SELECT
    'sessions "direct" avec un nom de campagne (incohérent)',
    CAST(SUM(CASE WHEN flag_direct_avec_campagne THEN 1 ELSE 0 END) AS INTEGER),
    CAST(COUNT(*) AS INTEGER)
FROM funnel;