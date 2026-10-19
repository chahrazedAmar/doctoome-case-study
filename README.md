# Doctoome – Étude de cas Data (questionnaire diabète de type 2)

## 1. Contexte (énoncé)

Doctoome a lancé une page d'accueil pour un questionnaire de sensibilisation au diabète de type 2
(5 questions). Les visiteurs arrivent par plusieurs canaux, puis partent, commencent ou terminent
le questionnaire. Chaque questionnaire terminé reçoit une catégorie analytique « selon ce questionnaire » :
`no_current_indication`, `possible_risk` ou `declared_diagnosed`.

Les données (6 tables Parquet : 26 000 sessions, 20 000 visiteurs, juin–août 2026) sont **synthétiques**.
Le questionnaire est **fictif, simplifié et non validé médicalement** : je n'en tire aucune conclusion médicale.
L'énoncé est volontairement ouvert : il demande de choisir et de justifier ses priorités.

**Mon cadrage (hypothèse) :** j'ai considéré que l'objectif d'une telle page est de transformer des
visiteurs en utilisateurs. Cet objectif vient du site public de Doctoome, pas des données :
aucun événement après le résultat n'est disponible.

**Constats principaux :**
1. **La croissance du trafic de l'été vient des visiteurs qui reviennent.** Les sessions de nouveaux visiteurs
   sont stables (9 572 en juin, 9 875 en juillet), les sessions de revenants sont multipliées par près de 5 (996 puis 4 878).
2. **Le questionnaire perd le plus de monde à la Q4** (13,5 % d'abandon, contre 2 à 6 % pour les autres questions),
   surtout sur mobile (16,9 % contre 8,0 % sur ordinateur).
3. **La règle de classement est très tolérante** : une réponse d'alerte isolée donne « aucune indication ».

## 1 bis. Priorisation

| Axe étudié | Pourquoi |
|---|---|
| Parcours (funnel) par question et appareil | Seul endroit où Doctoome peut agir directement |
| Sources d'acquisition, en volume **et** en qualité, à âge égal | Savoir où investir sans être trompée par l'âge ou l'appareil |
| Qualité des données | Toute conclusion en dépend (visiteur, fenêtre d'observation, variantes de noms) |
| Cohérence réponses → catégories | Vérifier que le résultat reflète les réponses |
| Analyse linguistique des questions | Le seul texte des données est le questionnaire |

Écartés après test : genre, jour, heure, région, campagnes (aucun effet solide, voir §7).

## 2. Reproduire l'analyse

Prérequis : Python 3.10 ou plus récent. Placer les six fichiers `.parquet` d'origine dans `data/`.

```bash
pip install -r requirements.txt
python scripts/01_explorer.py              # contrôles de qualité (affichage seulement)
python scripts/02_nettoyer.py              # crée data_clean/
python scripts/03_analyses_sql.py          # lance tous les sql/*.sql -> outputs/*.csv
python scripts/04_graphiques.py            # crée outputs/graph*.png
python scripts/05_analyse_linguistique.py  # analyse NLP des questions -> outputs/*.csv
python scripts/06_tests_significativite.py # tests du chi-deux -> outputs/06_tests_significativite.csv
```

Les scripts se lancent **dans cet ordre**, depuis le dossier du projet. Les chemins sont relatifs.
Dépendances : `pandas`, `pyarrow`, `duckdb`, `matplotlib`, `scipy`.

## 3. Arborescence

```
doctoome_case/
├── data/            données d'origine (jamais modifiées)
├── data_clean/      tables nettoyées (créées par 02)
├── scripts/         01 à 06 (Python)
├── sql/             01 à 14 (requêtes DuckDB sur les fichiers Parquet)
├── outputs/         résultats : CSV et graphiques PNG
├── requirements.txt
└── README.md
```

Note : dans `outputs/`, les préfixes **06, 07 et 08 existent chacun deux fois**, car les requêtes SQL (03)
et les scripts 05 et 06 numérotent chacun leurs fichiers. Ce sont des résultats différents.

## 4. Qualité des données et transformations

Principe : **on ne supprime presque rien, on corrige et on signale** (colonnes `flag_`).

| Problème | Décision |
|---|---|
| Genre : `F`, `Female`, `female` | Harmonisé en minuscules et abréviations ; vide devient `unknown` |
| Régions : accents, tirets, majuscules | Clé simplifiée, puis écriture la plus fréquente retenue |
| Sources : `Google`/`google`, `ChatGPT`/`chatgpt`/`AI Assistant`, `facebook`/`instagram` | Regroupées en `google_organic`, `ai_assistant`, `social` |
| Âge | 2026 − année de naissance ; `flag_mineur` ; `flag_annee_suspecte` (pics en 1946 et 2008) |
| `direct` avec un nom de campagne (219 sessions) | `flag_direct_avec_campagne` (incohérence) |
| Heures en UTC | Converties en heure de Paris ; semaine = lundi |
| Données arrêtées le 2 août à 16 h 44 UTC (679 sessions les 1er et 2 août) | `flag_periode_incomplete` ; exclue des tendances |
| Réponses modifiées dans une même session | On garde la **dernière** : la règle retrouve **100 %** des résultats officiels |
| 5 réponses mais aucun résultat (105 sessions) | `flag_5rep_sans_resultat` (anomalie de suivi) |
| `questionnaire_start` sans affichage de la Q1 ni réponse (893 sur 16 774, soit 5,3 %) | Conservés, signalés dans `sql/14` ; les comparaisons sensibles sont testées avec les deux définitions de « démarrer » |
| `first_seen_at` | Égal à la 1re session observée pour les 20 000 visiteurs (`sql/14`) : aucun historique avant juin |

## 5. Hypothèses

| Hypothèse | Statut | Éléments |
|---|---|---|
| H3 : `Google`/`google` = référencement naturel | Appuyée | 100 % des `google_ads` ont une campagne, 0 % des `google` ; profil identique à `google_organic` |
| `is_returning_visitor` dépend de la fenêtre d'observation | **Confirmée** | `first_seen_at` = 1re session pour 20 000 visiteurs sur 20 000 : la part de revenants monte par construction (`sql/13`, `sql/14`) |
| Un visiteur n'est pas une personne | Appuyée | Un même visiteur répond « oui » **et** « non » à des faits acquis (voir §6) |
| La Q5 est ambiguë (portée de « without ») | Appuyée | 319 personnes diagnostiquées sur 1 252 répondent « oui » à Q5 |
| L'abandon à la Q4 vient de sa forme sur mobile | Appuyée | Abandon mobile ≈ 2× ordinateur, uniquement à la Q4 |
| L'abandon à la Q4 vient aussi d'une pertinence perçue faible (« quel rapport avec le diabète ? ») | **Non prouvée** | Seule question sur le mode de vie ; pas de motif d'abandon dans les données |
| Les visites « social » sont en partie des clics accidentels | Partiellement appuyée | 48,6 % ne commencent pas ; 88 % sur mobile |
| Les visiteurs venus d'un assistant IA sont plus engagés | Partiellement appuyée | Ils démarrent bien plus (+11 pts) ; l'écart pour finir est faible et fragile (voir §7) |
| Problème de connexion selon les régions | **Écartée** | Pas d'effet régional (voir §7) |
| Questions en anglais | Expliquée par l'énoncé | Questions fictives et simplifiées pour l'exercice |

## 6. Résultats clés (source de chaque chiffre)

1. **Les nouveaux visiteurs n'augmentent pas.** Sessions de nouveaux visiteurs : 9 572 en juin, 9 875 en juillet.
   Sessions de revenants : 996 puis 4 878. La part de nouveaux passe de 90,6 % à 66,9 % **par construction de la mesure**
   (`first_seen_at` = 1re session pour tous). La complétion globale monte de 39,9 % (semaine du 1er juin) à 47,1 % (semaine du 20 juillet),
   alors que celle des nouveaux reste entre 38,8 % et 42,1 %. Source : `sql/05`, `sql/13`, `sql/14`, `graph5`.
2. **Parcours.** Sur 26 000 sessions, 35,5 % partent avant de commencer et 43,7 % terminent. La Q4 est la question où l'on perd
   le plus de monde : 13,5 % (Q1 2,0 %, Q2 5,0 %, Q3 5,8 %, Q5 4,8 %). Sur mobile 16,9 %, sur ordinateur 8,0 %, sur tablette 8,2 %.
   Temps médian : 21,0 s à la Q4 contre 13,4 à 13,6 s aux autres. Source : `sql/01`, `sql/02`, `outputs/07_linguistique_questions.csv`, `graph1`, `graph2`.
3. **« Rarement ou jamais » à la Q4 augmente avec l'âge** : 14,7 % chez les 18-24 ans, 36,7 % chez les 65 ans et plus.
   Cette réponse ajoute un point de risque : elle pèse donc plus sur le résultat des plus âgés. Source : `sql/12`.
4. **La règle de classement est très tolérante.** Règle reconstituée (elle reproduit 100 % des résultats) : Q1 = oui donne
   « diagnostiqué » ; sinon 1 point par réponse à risque (Q2, Q3, Q4 « rarement ou jamais », Q5), et 2 points ou plus
   donnent « risque possible ». Une seule réponse d'alerte donne donc « aucune indication » : Q5 = oui sans diagnostic,
   1 857 sessions dont 730 (39,3 %) ; Q2 = oui, 2 007 sessions dont 797 (39,7 %). « Pas sûr » et « préfère ne pas dire »
   comptent comme « non ». Source : `sql/10`, `05_analyse_linguistique.py`.
5. **Les sources.** Les assistants IA font démarrer plus : 74,7 % contre 63,3 % pour Google organique. Parmi ceux qui
   démarrent, l'écart pour finir est faible (70,8 % contre 68,2 %, voir §7). À âge égal, l'IA garde une meilleure complétion
   (50,8 à 55,6 % contre 42,7 à 44,9 %). Les réseaux sociaux : 48,6 % ne démarrent pas, 88 % sur mobile. Âge médian : social 36,
   IA 37, Google organique 44, Google Ads 52. L'e-mail complète le mieux (64,7 %) mais n'apporte que 22,8 % de nouveaux
   visiteurs : bonne qualité, pas d'acquisition. Source : `sql/03`, `sql/07`, `sql/08`, `sql/09`, `sql/11`, `graph6`, `graph7`.
6. **Visiteur ≠ personne.** Pour un fait acquis (« avez-vous déjà été… »), un même visiteur répond oui et non :
   Q1 20,3 %, Q3 40,5 %, Q5 28,2 %. Parmi les 1 503 visiteurs qui ont fait le questionnaire plusieurs fois,
   678 ont obtenu un résultat différent. Source : `outputs/08_coherence_visiteurs.csv`, `sql/06`.
7. **Les catégories ne mènent à aucune suite mesurable.** Les données s'arrêtent au résultat : on ne peut pas savoir si le
   visiteur s'inscrit ou consulte. L'indicateur principal proposé (résultat → inscription) suppose de collecter de nouveaux
   événements (voir §9).

## 7. Tests de significativité (test du chi-deux)

Seuil : p < 0,05. Un écart n'est « solide » que si p < 0,01. Script : `06_tests_significativite.py`.

| Comparaison | p-value | Lecture |
|---|---|---|
| Abandon Q4 : mobile / ordinateur / tablette | < 0,0001 | **Réel.** Intervalles de confiance à 95 % : mobile [16,0 ; 17,6], ordinateur [7,2 ; 8,7] |
| « Rarement ou jamais » (Q4) selon l'âge | < 0,0001 | **Réel** |
| Démarrage et complétion selon la source | < 0,0001 | **Réel** |
| Démarrage : IA / Google organique | < 0,0001 | **Réel** (74,7 % / 63,3 %) |
| Finir (parmi les démarrés) : IA / Google organique | 0,039 (0,073 si « démarrer » = voir la Q1) | **Fragile** : dépend de la définition |
| Campagnes Google Ads | 0,026 (0,13 si « démarrer » = voir la Q1) | **Fragile** : non retenu |
| Abandon Q4 selon la région | 0,19 (0,62 sur mobile) | **Écarté** |
| Genre, jour de la semaine, heure | de 0,11 à 0,82 | **Écartés** |

Pistes testées et écartées : région/connexion, campagnes Ads, genre, jour et heure.

## 8. Analyse linguistique (NLP)

`05_analyse_linguistique.py` relie la **forme** des questions au **comportement** : longueur, temporalité
(« ever » = fait acquis, « usually » = habitude), négation, deux idées dans une question, seuil à calculer
(« at least 30 minutes »). La Q4 est la seule à cumuler habitude, calcul d'un seuil et réponses longues
(19,5 caractères en moyenne, contre 4 à 7 ailleurs) : c'est aussi la plus abandonnée et la plus lente.
La Q5 contient une négation (« without ») dont la portée est ambiguë. Les Q2 et Q3 posent deux idées à la fois.
Le test de cohérence par visiteur (§6, point 6) confirme que les faits acquis ne sont pas stables d'une visite à l'autre.
Des reformulations vont dans le sens d'un langage patient : questions courtes, oui/non, exemples.

## 9. Réponses aux quatre questions

**1. Résultats clés** : voir §6.

**2. Questions sans réponse**
- Pourquoi abandonne-t-on à la Q4 : forme, pertinence perçue, ou gêne à répondre ?
- Que font les gens après le résultat ? (aucune donnée)
- L'IA amène-t-elle des visiteurs plus motivés, ou les oriente-t-elle mieux ?
- Les visites « social » sont-elles des clics accidentels ?
- Combien de personnes réelles se cachent derrière les visiteurs ?

**3. Données à collecter**
- Événements après le résultat : clic vers un praticien, création de compte, rendez-vous
- Motif d'abandon (mini-question de sortie)
- Temps de chargement et erreurs techniques par appareil
- Identifiant de compte (pour dédupliquer les visiteurs)
- Coût par campagne ; version du questionnaire (pour les tests A/B)
- Historique avant juin (pour définir correctement « nouveau » et « revenant »)

**4. À suivre sur 12 mois**
- **Indicateur principal : résultat → inscription ou rendez-vous**
- Taux de démarrage par source
- Abandon par question et par appareil (Q4 sur mobile en priorité)
- Nombre de **nouveaux** visiteurs par mois, sur une fenêtre fixe
- Part des réponses d'alerte classées « aucune indication »
- Part des démarrages sans affichage de la Q1 (fiabilité du suivi)
- Coût par inscription par source ; tests A/B sur la Q4 et la Q5

## 10. Limites

- Les données sont synthétiques (énoncé) : leur régularité vient probablement de la génération (9 régions seulement,
  de 2 700 à 2 900 sessions chacune, l'Île-de-France comme les autres ; entre 1 000 et 1 100 sessions par heure,
  y compris la nuit). Je n'en tire pas de conclusion sur le comportement réel.
- La période annoncée est juin–août, mais les données s'arrêtent le 2 août.
- L'analyse est descriptive : elle ne prouve pas de causalité.
- Plusieurs tests ont été faits sans correction : un résultat proche de 0,05 reste à confirmer, et deux conclusions
  dépendent de la définition de « démarrer » (voir §7).
- Si les données étaient réelles : ce seraient des données de santé (RGPD), avec des mineurs signalés.

## 11. Usage de l'IA

J'ai utilisé un assistant IA (Claude) pour structurer l'analyse, écrire le code (Python et SQL) et vérifier mes calculs.
J'ai exécuté tous les scripts moi-même et vérifié que les résultats se reproduisent.
Je m'appuie sur ce travail pour l'entretien : j'apprends chaque étape pour pouvoir l'expliquer et la modifier.