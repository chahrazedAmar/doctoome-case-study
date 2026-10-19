-- 12_q4_selon_age.sql
-- Q4 (activité physique) : quelle part répond "rarely_or_never" selon l'âge ?
-- Pourquoi c'est important : cette réponse vaut 1 point de risque dans la règle de classement,
-- donc elle fait monter le "risque" des plus âgés.
-- Unité : la SESSION qui a répondu à la Q4 (dernière réponse gardée).
-- On exclut les mineurs et les années de naissance suspectes (1946, 2008), comme dans 04.
SELECT
    f.age_group                                                                         AS tranche_age,
    COUNT(*)                                                                            AS reponses_q4,
    CAST(SUM(CASE WHEN a.answer_value = 'rarely_or_never' THEN 1 ELSE 0 END) AS INTEGER) AS rarement_ou_jamais,
    ROUND(100.0 * AVG(CASE WHEN a.answer_value = 'rarely_or_never' THEN 1 ELSE 0 END), 1) AS pct_rarement_ou_jamais
FROM answers a
JOIN funnel f ON f.session_id = a.session_id
WHERE a.question_number = 4
  AND f.age_group IS NOT NULL
  AND NOT f.flag_mineur
  AND NOT f.flag_annee_suspecte
GROUP BY f.age_group
ORDER BY f.age_group;