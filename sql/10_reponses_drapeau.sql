-- 10_reponses_drapeau.sql
-- Les personnes NON diagnostiquées (Q1 différent de "yes") qui répondent "yes" à la Q5
-- (un soignant leur a déjà dit que leur glycémie était trop élevée) : quel résultat reçoivent-elles ?
-- Idem pour la Q2 (symptômes). La règle demande 2 réponses à risque : une seule ne suffit pas.
WITH reponses AS (
    -- on met les 5 réponses d'une session sur une seule ligne (pivot "à la main")
    SELECT
        session_id,
        MAX(CASE WHEN question_number = 1 THEN answer_value END) AS q1,
        MAX(CASE WHEN question_number = 2 THEN answer_value END) AS q2,
        MAX(CASE WHEN question_number = 5 THEN answer_value END) AS q5
    FROM answers
    GROUP BY session_id
)
SELECT
    'Q5 = yes (glycémie déjà signalée)'                                          AS signal,
    COUNT(*)                                                                     AS personnes,
    CAST(SUM(CASE WHEN o.outcome_category = 'no_current_indication' THEN 1 ELSE 0 END) AS INTEGER) AS classees_aucune_indication,
    ROUND(100.0 * AVG(CASE WHEN o.outcome_category = 'no_current_indication' THEN 1 ELSE 0 END), 1) AS pct
FROM reponses r JOIN outcomes o ON o.session_id = r.session_id
WHERE r.q1 <> 'yes' AND r.q5 = 'yes'
UNION ALL
SELECT
    'Q2 = yes (symptômes)',
    COUNT(*),
    CAST(SUM(CASE WHEN o.outcome_category = 'no_current_indication' THEN 1 ELSE 0 END) AS INTEGER),
    ROUND(100.0 * AVG(CASE WHEN o.outcome_category = 'no_current_indication' THEN 1 ELSE 0 END), 1)
FROM reponses r JOIN outcomes o ON o.session_id = r.session_id
WHERE r.q1 <> 'yes' AND r.q2 = 'yes';