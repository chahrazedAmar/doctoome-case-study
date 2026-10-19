-- 01_funnel_global.sql
-- Funnel global : combien de sessions passent chaque étape, et quel % on perd à chaque étape.
-- Unité de comptage : la SESSION (une visite).
WITH etapes AS (
    SELECT 1 AS ordre, '0. Arrivée sur la page' AS etape, COUNT(*)                         AS sessions FROM funnel UNION ALL
    SELECT 2, '1. Début du questionnaire', SUM(CASE WHEN start   THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 3, '2. Question 1 affichée',    SUM(CASE WHEN vue_q1  THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 4, '3. Réponse Q1',             SUM(CASE WHEN rep_q1  THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 5, '4. Réponse Q2',             SUM(CASE WHEN rep_q2  THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 6, '5. Réponse Q3',             SUM(CASE WHEN rep_q3  THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 7, '6. Réponse Q4',             SUM(CASE WHEN rep_q4  THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 8, '7. Réponse Q5',             SUM(CASE WHEN rep_q5  THEN 1 ELSE 0 END) FROM funnel UNION ALL
    SELECT 9, '8. Questionnaire terminé',  SUM(CASE WHEN complete THEN 1 ELSE 0 END) FROM funnel
)
SELECT
    etape,
    CAST(sessions AS INTEGER) AS sessions,
    -- LAG() = valeur de la ligne précédente -> permet de calculer la perte entre 2 étapes
    ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY ordre), 1)     AS pct_des_arrivees,
    ROUND(100.0 * (1 - sessions / LAG(sessions) OVER (ORDER BY ordre)), 1)      AS pct_perdu_vs_etape_prec
FROM etapes
ORDER BY ordre;