-- 06_visiteurs_repetes.sql
-- Combien de visiteurs ont terminé le questionnaire plusieurs fois,
-- et combien ont obtenu des résultats différents d'une fois à l'autre ?
WITH par_visiteur AS (
    SELECT visitor_id,
           COUNT(*)                          AS nb_questionnaires,
           COUNT(DISTINCT outcome_category)  AS nb_resultats_differents
    FROM outcomes
    GROUP BY visitor_id
)
SELECT
    nb_questionnaires,
    COUNT(*)                                                    AS visiteurs,
    CAST(SUM(CASE WHEN nb_resultats_differents > 1 THEN 1 ELSE 0 END) AS INTEGER) AS dont_resultat_qui_change
FROM par_visiteur
GROUP BY nb_questionnaires
ORDER BY nb_questionnaires;