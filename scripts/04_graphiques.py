# =============================================================
# 04_graphiques.py
# ÉTAPE 4 : créer les graphiques pour les slides, à partir des CSV de l'étape 3
# Principe : UN message par graphique. La couleur vive = ce qu'on veut montrer, le gris = le reste.
# Lancer depuis doctoome_case :  python scripts/04_graphiques.py
# =============================================================

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")              # dessine dans des fichiers, sans ouvrir de fenêtre
import matplotlib.pyplot as plt

# --- Chemins ---
PROJET = Path(__file__).parent.parent
OUT = PROJET / "outputs"

# --- Couleurs : une couleur d'accent + du gris ---
ACCENT = "#C2185B"     # rose foncé : ce qui compte
GRIS = "#B0B0B0"       # le reste
TEXTE = "#333333"

# --- Style commun à tous les graphiques ---
plt.rcParams.update({
    "font.size": 12,
    "axes.spines.top": False,      # on enlève les bordures inutiles (haut et droite)
    "axes.spines.right": False,
    "axes.edgecolor": GRIS,
    "axes.labelcolor": TEXTE,
    "xtick.color": TEXTE,
    "ytick.color": TEXTE,
})


def enregistrer(fig, nom):
    """Enregistre le graphique en PNG (haute qualité) dans outputs/ puis le ferme."""
    fig.tight_layout()                                   # évite que les textes se chevauchent
    fig.savefig(OUT / nom, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Graphique créé :", nom)


# =============================================================
# GRAPHIQUE 1 : le funnel (où perd-on les visiteurs ?)
# =============================================================
funnel = pd.read_csv(OUT / "01_funnel_global.csv")

fig, ax = plt.subplots(figsize=(10, 5.5))
# Barres horizontales ; on inverse l'ordre pour avoir l'arrivée en haut
couleurs = [ACCENT if "Q4" in e else GRIS for e in funnel["etape"]]   # on met en valeur la Q4
ax.barh(funnel["etape"][::-1], funnel["sessions"][::-1], color=couleurs[::-1])

# On écrit le % des arrivées au bout de chaque barre
for i, (n, pct) in enumerate(zip(funnel["sessions"][::-1], funnel["pct_des_arrivees"][::-1])):
    ax.text(n + 200, i, f"{n:,} ({pct:.0f} %)".replace(",", " "), va="center", color=TEXTE)

ax.set_xlabel("Nombre de sessions")
ax.set_xlim(0, funnel["sessions"].max() * 1.22)
ax.set_title("Sur 100 visiteurs, 44 terminent le questionnaire\n"
             "La question 4 provoque la plus forte perte (-13,5 %)", loc="left", color=TEXTE)
enregistrer(fig, "graph1_funnel.png")

# =============================================================
# GRAPHIQUE 2 : abandon par question selon l'appareil
# =============================================================
abandon = pd.read_csv(OUT / "02_abandon_par_question_appareil.csv").set_index("appareil")
questions = ["abandon_q2", "abandon_q3", "abandon_q4", "abandon_q5"]
etiquettes = ["Q2", "Q3", "Q4", "Q5"]

fig, ax = plt.subplots(figsize=(10, 5.5))
for appareil, couleur, style in [("mobile", ACCENT, "-"), ("desktop", GRIS, "--"), ("tablet", GRIS, ":")]:
    valeurs = abandon.loc[appareil, questions]
    ax.plot(etiquettes, valeurs, marker="o", color=couleur, linestyle=style, linewidth=2.5, label=appareil)
    ax.text(3.1, valeurs.iloc[-1], appareil, va="center", color=couleur)   # nom au bout de la ligne

ax.set_ylabel("% d'abandon à cette question")
ax.set_ylim(0, 20)
ax.set_title("Sur mobile, 1 personne sur 6 abandonne à la question 4\n"
             "soit 2 fois plus que sur ordinateur", loc="left", color=TEXTE)
enregistrer(fig, "graph2_abandon_q4_mobile.png")

# =============================================================
# GRAPHIQUE 3 : taux de complétion par source
# =============================================================
sources = pd.read_csv(OUT / "03_conversion_par_source.csv").sort_values("pct_completion")

fig, ax = plt.subplots(figsize=(10, 5.5))
couleurs = [ACCENT if s in ("email", "referral", "social") else GRIS for s in sources["source"]]
ax.barh(sources["source"], sources["pct_completion"], color=couleurs)
for i, (pct, n) in enumerate(zip(sources["pct_completion"], sources["sessions"])):
    ax.text(pct + 0.8, i, f"{pct:.0f} %  ({n:,} sessions)".replace(",", " "), va="center", color=TEXTE)

ax.set_xlabel("% des sessions qui terminent le questionnaire")
ax.set_xlim(0, 85)
ax.set_title("L'email et les sites partenaires convertissent 2 fois mieux que les réseaux sociaux",
             loc="left", color=TEXTE)
enregistrer(fig, "graph3_completion_par_source.png")

# =============================================================
# GRAPHIQUE 4 : part de "risque possible" par tranche d'âge
# =============================================================
age = pd.read_csv(OUT / "04_resultats_par_age.csv")

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.bar(age["tranche_age"], age["pct_risque_possible"], color=ACCENT, label="Risque possible")
ax.bar(age["tranche_age"], age["pct_diagnostic_declare"], bottom=age["pct_risque_possible"],
       color=GRIS, label="Diagnostic déclaré")
for i, pct in enumerate(age["pct_risque_possible"]):
    ax.text(i, pct / 2, f"{pct:.0f} %", ha="center", color="white", fontweight="bold")

ax.set_ylabel("% des visiteurs (dernier questionnaire)")
ax.legend(frameon=False)
ax.set_title("La part de « risque possible » est 3,5 fois plus élevée chez les 65+ que chez les 18-24 ans\n"
             "(résultat du questionnaire, pas un diagnostic médical)", loc="left", color=TEXTE, fontsize=11)
enregistrer(fig, "graph4_risque_par_age.png")

# =============================================================
# GRAPHIQUE 5 : évolution par semaine, NOUVEAUX vs REVENANTS
# Piège : "is_returning_visitor" ne regarde que la période fournie -> la part de revenants
# monte mécaniquement. On sépare donc les nouveaux visiteurs pour voir la vraie tendance.
# =============================================================
hebdo = pd.read_csv(OUT / "05_evolution_hebdo.csv")
semaines = pd.to_datetime(hebdo["semaine_du"]).dt.strftime("%d/%m")    # format court : 01/06

# 2 graphiques côte à côte (1 ligne, 2 colonnes)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))

# --- À gauche : sessions par semaine, empilées (nouveaux en bas, revenants au-dessus) ---
ax1.bar(semaines, hebdo["sessions_nouveaux"], color=ACCENT, label="Nouveaux visiteurs")
ax1.bar(semaines, hebdo["sessions_revenants"], bottom=hebdo["sessions_nouveaux"],
        color=GRIS, label="Revenants")
ax1.set_ylabel("Sessions par semaine")
ax1.set_title("Sessions : seuls les revenants augmentent", loc="left", color=TEXTE, fontsize=11)
ax1.legend(frameon=False, loc="upper left")
ax1.tick_params(axis="x", rotation=45)

# --- À droite : taux de complétion, global vs nouveaux visiteurs ---
ax2.plot(semaines, hebdo["pct_completion"], color=GRIS, linestyle="--", marker="o",
         linewidth=2, label="Tous les visiteurs")
ax2.plot(semaines, hebdo["pct_completion_nouveaux"], color=ACCENT, marker="o",
         linewidth=2.5, label="Nouveaux visiteurs")
ax2.set_ylabel("% de complétion")
ax2.set_ylim(30, 50)
ax2.set_title("Complétion : stable à ~40 % chez les nouveaux", loc="left", color=TEXTE, fontsize=11)
ax2.legend(frameon=False, loc="upper left")
ax2.tick_params(axis="x", rotation=45)

fig.suptitle("L'acquisition de nouveaux visiteurs n'a pas progressé cet été : la hausse apparente vient des revenants\n"
             "(semaine du 27/07 : 5 jours ; 1er-2 août exclus car incomplets)",
             x=0.01, ha="left", color=TEXTE, fontsize=12)
enregistrer(fig, "graph5_evolution_hebdo.png")

# =============================================================
# GRAPHIQUE 6 : QUANTITÉ vs QUALITÉ par source (nouveaux visiteurs)
# Axe horizontal = combien de questionnaires terminés par de NOUVEAUX visiteurs (le volume)
# Axe vertical   = % des visiteurs qui terminent (la qualité)
# Taille de la bulle = nombre de sessions
# =============================================================
vq = pd.read_csv(OUT / "07_volume_vs_qualite_sources.csv")
noms = {"google_organic": "Google naturel", "google_ads": "Google Ads", "ai_assistant": "Assistants IA",
        "social": "Réseaux sociaux", "referral": "Sites partenaires", "direct": "Direct",
        "email": "Email", "other": "Autres"}

fig, ax = plt.subplots(figsize=(10, 6))
# Les lignes pointillées = moyennes : elles découpent le graphique en 4 zones
moy_x = vq["termines_nouveaux"].mean()
moy_y = 100 * vq["questionnaires_termines"].sum() / vq["sessions"].sum()   # taux global
ax.axvline(moy_x, color=GRIS, linestyle="--", linewidth=1)
ax.axhline(moy_y, color=GRIS, linestyle="--", linewidth=1)

for _, r in vq.iterrows():
    star = r["source"] == "ai_assistant"                     # la source à mettre en avant
    ax.scatter(r["termines_nouveaux"], r["pct_completion"], s=r["sessions"] / 6,
               color=ACCENT if star else GRIS, alpha=0.85 if star else 0.6, edgecolor="white")
    ax.annotate(noms.get(r["source"], r["source"]), (r["termines_nouveaux"], r["pct_completion"]),
                xytext=(8, 8), textcoords="offset points", color=ACCENT if star else TEXTE,
                fontweight="bold" if star else "normal")

# Noms des 4 zones, dans les coins
ax.text(0.98, 0.97, "Volume + qualité : à développer", transform=ax.transAxes, ha="right", va="top", color=ACCENT, fontsize=10)
ax.text(0.02, 0.97, "Qualité, peu de nouveaux : à multiplier", transform=ax.transAxes, ha="left", va="top", color=GRIS, fontsize=10)
ax.text(0.98, 0.03, "Volume, qualité moyenne : à optimiser", transform=ax.transAxes, ha="right", va="bottom", color=GRIS, fontsize=10)
ax.text(0.02, 0.03, "Peu de volume, faible qualité", transform=ax.transAxes, ha="left", va="bottom", color=GRIS, fontsize=10)

ax.set_xlabel("Questionnaires terminés par de NOUVEAUX visiteurs (volume)")
ax.set_ylabel("% des visiteurs qui terminent (qualité)")
ax.set_xlim(0, vq["termines_nouveaux"].max() * 1.2)
ax.set_ylim(20, 75)
ax.set_title("Google apporte le volume, les assistants IA combinent volume et qualité\n"
             "L'email convertit bien mais touche peu de nouveaux visiteurs (taille des bulles = sessions)",
             loc="left", color=TEXTE, fontsize=11)
enregistrer(fig, "graph6_volume_vs_qualite.png")


# =============================================================
# GRAPHIQUE 7 : répartition par âge de chaque source
# Message : les assistants IA amènent un public nettement plus jeune que Google Ads.
# Barres horizontales "empilées" : chaque barre = 100 % des visiteurs d'une source.
# =============================================================
ages = pd.read_csv(OUT / "11_age_par_source.csv").iloc[::-1]   # inversé : la plus jeune en haut
noms_src = {"google_organic": "Google naturel", "google_ads": "Google Ads", "ai_assistant": "Assistants IA",
            "social": "Réseaux sociaux", "referral": "Sites partenaires", "direct": "Direct", "email": "Email"}
etiquettes_src = [f"{noms_src.get(s, s)} ({a} ans)" for s, a in zip(ages["source"], ages["age_median"])]

tranches = [("pct_18_34", "18-34 ans", ACCENT), ("pct_35_49", "35-49 ans", "#E8A0BF"),
            ("pct_50_64", "50-64 ans", "#C8C8C8"), ("pct_65_plus", "65 ans et +", "#7A7A7A")]

fig, ax = plt.subplots(figsize=(10, 5.5))
gauche = [0] * len(ages)                                  # position de départ de chaque morceau
for col, label, couleur in tranches:
    ax.barh(etiquettes_src, ages[col], left=gauche, color=couleur, label=label)
    for i, (g, v) in enumerate(zip(gauche, ages[col])):   # on écrit le % si le morceau est assez large
        if v >= 7:
            ax.text(g + v / 2, i, f"{v:.0f} %", ha="center", va="center",
                    color="white" if couleur in (ACCENT, "#7A7A7A") else TEXTE, fontsize=10)
    gauche = [g + v for g, v in zip(gauche, ages[col])]

ax.set_xlim(0, 100)
ax.set_xlabel("% des visiteurs de la source (âge déclaré, médiane entre parenthèses)")
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
ax.set_title("Assistants IA et réseaux sociaux amènent les publics les plus jeunes (36-37 ans),\n"
             "Google Ads le plus âgé (52 ans) : des publics différents, des messages différents", loc="left", color=TEXTE)
enregistrer(fig, "graph7_age_par_source.png")