-- 02_abandon_par_question_appareil.sql
-- Pour chaque appareil : % de personnes qui abandonnent à chaque question
-- (parmi celles qui ont répondu à la question précédente).
SELECT
    device_type                                                              AS appareil,
    COUNT(*) FILTER (WHERE rep_q1)                                           AS ont_repondu_q1,
    ROUND(100.0 * (1 - COUNT(*) FILTER (WHERE rep_q2) / COUNT(*) FILTER (WHERE rep_q1)), 1) AS abandon_q2,
    ROUND(100.0 * (1 - COUNT(*) FILTER (WHERE rep_q3) / COUNT(*) FILTER (WHERE rep_q2)), 1) AS abandon_q3,
    ROUND(100.0 * (1 - COUNT(*) FILTER (WHERE rep_q4) / COUNT(*) FILTER (WHERE rep_q3)), 1) AS abandon_q4,
    ROUND(100.0 * (1 - COUNT(*) FILTER (WHERE rep_q5) / COUNT(*) FILTER (WHERE rep_q4)), 1) AS abandon_q5
FROM funnel
GROUP BY device_type
ORDER BY abandon_q4 DESC;