-- 04_resultats_par_age.sql
-- Répartition des résultats par tranche d'âge.
-- Unité : le VISITEUR (on garde son DERNIER questionnaire), car certains l'ont fait plusieurs fois.
-- On exclut les mineurs et les années de naissance suspectes (1946, 2008).
WITH dernier AS (
    SELECT o.visitor_id, o.outcome_category,
           -- ROW_NUMBER numérote les questionnaires d'un visiteur du plus récent (1) au plus ancien
           ROW_NUMBER() OVER (PARTITION BY o.visitor_id ORDER BY o.completed_at DESC) AS rang
    FROM outcomes o
)
SELECT
    v.age_group                                                                         AS tranche_age,
    COUNT(*)                                                                            AS visiteurs,
    ROUND(100.0 * AVG(CASE WHEN d.outcome_category = 'possible_risk'         THEN 1 ELSE 0 END), 1) AS pct_risque_possible,
    ROUND(100.0 * AVG(CASE WHEN d.outcome_category = 'declared_diagnosed'    THEN 1 ELSE 0 END), 1) AS pct_diagnostic_declare,
    ROUND(100.0 * AVG(CASE WHEN d.outcome_category = 'no_current_indication' THEN 1 ELSE 0 END), 1) AS pct_aucune_indication
FROM dernier d
JOIN visitors v ON v.visitor_id = d.visitor_id
WHERE d.rang = 1
  AND v.age_group IS NOT NULL
  AND NOT v.flag_mineur
  AND NOT v.flag_annee_suspecte
GROUP BY v.age_group
ORDER BY v.age_group;