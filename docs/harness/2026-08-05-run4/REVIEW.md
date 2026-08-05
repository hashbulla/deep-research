# Skill Harness Review — deep-research — 2026-08-05

> **Verdict : PASS — 7.61 / 10.** 0 CRITICAL · 5 WARNING · 17 ADVISORY · 0 UNKNOWN. Run #4 contre cette cible ; harness **UNCALIBRATED** — revue humaine due. Pipeline : Analyst → Strategist → Critic (worktree-isolé, 87 appels routeur vifs, 10 suites CI exécutées, 3 sondes adverses contre le gate) → Citation Grounder (append-only vérifié par diff : 0 modification, 42 additions pures). Cible : branche `chantier/github-topic-facet`, HEAD `11a0439`. Dossier de preuve brut : `.harness-staging/` (conservé pour la revue de calibration).

## Spec inféré (confiance MEDIUM)

Pipeline de recherche 7 phases via la suite Tavily MCP émettant **exactement cinq artefacts écrits atomiquement en fin de Phase 6**, gradation NATO A–F × 1–6 avec routage des claims par crédibilité, gates arithmétiques re-vérifiés par `scripts/verify_gates.py` (verdicts JSON cités dans le message final), deux adversaires décorrélés sur un autre modèle (juge de fidélité Phase 5, critic de complétude Phase 5b), manifeste solution-space universel. Routage : `/deep-research` + formulations EN/FR d'une recherche planifiée multi-sources graduée ; frontières vives = la commande user-scope `/research` et le sibling plugin-namespacé. Confiance plafonnée MEDIUM : pas de `evals/hero-queries.md` (guide harness §3). Spec complet : `.harness-staging/skill_spec.md`.

## Scores

| Dim | Nom | Poids | Score | |
|---|---|---|---|---|
| 1 | Description routing precision | 2.0× | **8.0** | ✅ PASS |
| 2 | Tax-test compliance | 1.5× | **7.0** | ✅ PASS |
| 3 | Token-budget hygiene | 1.5× | **7.5** | ✅ PASS |
| 4 | Eval coverage | 1.5× | **7.0** | ✅ PASS |
| 5 | Append-mostly hygiene | 1.0× | **9.0** | ✅ PASS |
| 6 | Cross-skill territorial conflicts | 1.0× | **9.0** | ✅ PASS |
| 7 | Description economy | 1.0× | **6.0** | ⚠️ WARN |

**Overall = 72.25 / 9.5 = 7.61 / 10 — PASS** (≥7.0 ; aucune dimension <5.0 ; matrice D1 exécutée).

Conditions du gate toutes vérifiées empiriquement. **Une seule dépendance critique du verdict** : le check 17 de `lint_skill.py` (« deep-research = nom interdit ») est un faux positif d'instrument. Vérifié post-advisor contre les trois surfaces qui définissent « reserved », pas seulement la structure interne du fichier de noms : (1) `critic-rubric.md:27` est l'**unique** occurrence de « reserved » dans le rubric, sans définition ni pointeur vers `forbidden_names.txt`, et sa clause gouverne la *description* — qui ne contient ni `claude` ni `anthropic` ; (2) `lint_skill.py:443` **exclut par construction** `{claude, anthropic}` des offenders du check 17 — l'instrument lui-même sépare réservation Anthropic (`forbidden_names.txt:5-6`) et prévention de collision (`:33`, où vit `deep-research`) ; (3) `lint_skill.py:441-442` skippe l'auto-collision quand `name == folder_name` — le check n'a tiré que parce que le **worktree** s'appelle `github-topic-facet` ; dans le déploiement réel (`~/.claude/skills/deep-research/`) il ne tire jamais. Si le nom avait été réellement réservé, la clause Fail du rubric forçait CRITICAL/FAIL malgré le 7.61.

Matrice de loading (`opus,sonnet,haiku`, backend cli, cache froid) : opus 15/15 pos · 15/15 neg ; sonnet 14/15 pos · 15/15 neg ; haiku 15/15 pos · 13/13 neg (2 NO_VERDICT, gap de harness, jamais un miss). **Zéro fuite de négatif sur 43 verdicts réels** ; aucun release-blocker (`neg-07`/`neg-08`/`neg-15`) échoué. Comptes réconciliés (deux unités, vérifiées sur `loading_matrix.json`) : **90 cellules de verdict** (30 lignes × 3 modèles, aucune droppée) = 88 verdicts réels + 2 NO_VERDICT, produites par **87 appels frais** — 29 prompts uniques × 3, le doublon byte-identique `neg-08`≡`neg-15` étant dédupliqué par le runner.

## Findings par sévérité

### CRITICAL — aucun

### WARNING (5)

Les findings 1–3 partagent **une racine unique** : le gate, le golden et la référence mandatée encodent tous une règle plus faible que la doctrine de `references/github-research.md:2` (≥3 combinaisons `topic:`). La claim du commit « Suite complète verte, schémas valides » est **vraie et confirmée indépendamment** — et c'est précisément parce que la suite est verte que la divergence est invisible.

---

**1. [DIM-4] Rule 7b accepte un manifeste à zéro facette `topic:` (mesuré)**
`scripts/verify_gates.py:104` (`GITHUB_NATIVE_QUERY`) + `:552-560` (Rule 7b), contre `references/github-research.md:2`.
La doctrine mandate ≥3 combinaisons `topic:` triées par étoiles, AVANT le sharding par bandes. Rule 7b n'exige que **≥1** requête matchant une alternation qui inclut les bandes `stars:` et `gh api`/`gh search`. **Sonde A** (star-band seul, zéro topic) → `PASS, 0 violations`. **Sonde C** (une seule combinaison topic) → PASS. Le gate ferme l'*instance* mesurée (prose seule) mais pas la *classe* que sa propre analyse racine nomme (`gotchas-log.md:23` : les topics sont « le seul axe immunisé contre "mes mots encodent mon hypothèse" » — propriété qu'une bande `stars:` sur mots-clés n'a pas). Le seul check qui fermerait la classe — `e2e-15` check 2 — vit dans la suite que le runner ne peut pas exécuter.
**Fix** : Rule 7b exige ≥3 valeurs de facette `topic:` **distinctes** quand `key == "open-source"` et `status ∈ {swept, empty}` ; scinder le regex en `GITHUB_TOPIC_FACET` (`topic:[\w.\-]+`) + `GITHUB_NATIVE_QUERY` ; compter les slugs distincts sur `live_queries` ; violation dédiée pour le cas <3. Ajouter `probe-starband-only` en fixture #13 + ligne d'attente dans `tests/check-solution-space.sh`.
*Citations : Anthropic “Demystifying evals” (string-match ≠ outcome verification ; les regression evals « protect against backsliding ») — Tier 1, A1.*

**2. [DIM-2] La lecture mandatée de Phase 1b prescrit des requêtes que le gate rejette désormais**
`references/solution-space.md:38` (primaire) ; `:21` ; `references/anti-patterns.md:85` (B14).
`SKILL.md:79` mandate la lecture de `solution-space.md` sur toute géométrie applicable ; sa ligne 38 prescrit quatre gabarits **prose** (`"<capability> client library"`, …) — un agent qui la suit à la lettre écrit un manifeste qui **échoue Rule 7b**. Le commit n'a pas touché ce fichier. La cellule Instrument `:21` résume encore `github-research.md` sans la facette topic ; B14 idem. `github-research.md` est gaté sur « tooling-discovery sub-question » alors que Rule 7b tire sur un ensemble strictement plus large. `check-cross-references.sh` ne peut pas l'attraper (il vérifie l'existence des cibles, pas l'accord sémantique). Mitigation réelle : la chaîne de violation nomme les formes acceptées — d'où WARNING, pas CRITICAL.
**Fix** : (1) préfixer les formes GitHub-natives dans la colonne « use » de `:38` et déplacer `site:github.com` en « never » ; (2) réécrire la cellule Instrument `:21` en tête « topic-facet sweep first (≥3), then star-band sharding… » ; (3) une phrase à B14 nommant la facette topic comme axe indépendant de la langue.
*Citations : platform.claude.com best-practices (« Consistent terminology » en ship gate) ; agentskills.io best-practices (read-gates scopés, « conflicting instructions ») — Tier 1, A1.*

**3. [DIM-4] Le golden corrigé porte 2 des ≥3 combinaisons mandatées**
`tests/fixtures/solution-space/valid.json:63-67`.
Trois requêtes, **exactement 2 combinaisons topic distinctes** contre les ≥3 de la doctrine. `gotchas-log.md:21` nomme ce fichier « the thing a maintainer copies » et diagnostique exactement cette forme de piège — qui **récidive un niveau plus haut dans le même commit** : le golden a été corrigé de « prose » vers « GitHub-natif », pas vers « conforme à la doctrine ».
**Fix** : ajouter une 3e combinaison distincte, puis (une fois Rule 7b renforcée) asserter dans `check-solution-space.sh` que le golden porte ≥3 — épingler le golden à la doctrine, pas seulement au gate.
*Citations : Anthropic “Demystifying evals” (« false confidence », dérive de ground truth) — Tier 1, A1 ; platform.claude.com best-practices (rôle d'exemple de référence) — Tier 2, B2 (porte le rôle, pas le seuil ≥3).*

**4. [DIM-1] L'unique miss positif de la matrice sonde une surface qui ne peut structurellement pas router**
`evals/loading.jsonl:6` (`pos-06`), cross-ref `SKILL.md:3` vs `SKILL.md:24`.
Sonnet rend `none` sur « benchmark Postgres vs DuckDB… with citations » — phrase présente **uniquement** dans la liste Trigger du corps (`:24`), que `:19` désavoue comme routeur (« not a second router »). `pos-05` (phrase verbatim de la description) passe 3/3. C'est le mode d'échec « Fragile » que la cible définit elle-même (`evals/rubric.md:22`).
**Fix** (au choix) : (a) ajouter la branche benchmark/citations à la description (299 chars de marge sous le cap) + re-run de la matrice ; (b) amender le champ `boundary` de `pos-06` pour qu'il cesse d'impliquer une surface de routage inexistante.
*Citations : platform.claude.com overview (Level 1 always-loaded vs Level 2 on-trigger) ; agentskills.io optimizing-descriptions (« the description carries the entire burden of triggering ») ; docs.anthropic.com claude-code/skills — Tier 1, A1.*

**5. [DIM-7] Paire de triggers synonymes FR/EN dans la description toujours-chargée** — **CONTESTÉ, puis RÉSOLU PAR ABLATION (2026-08-05, post-rapport)**
`SKILL.md:3` : `"deep research on X"` / `"recherche approfondie sur X"` = la même branche écrite deux fois (~30 tokens d'index). Slip nommé verbatim par le rubric D7. Défense d'auteur documentée (opérateur francophone, 3 fixtures positives FR toutes 3/3) — un pass ne prouve pas la nécessité, seule une ablation le ferait.
**Résolution mesurée (adjudication Victor : ablation immédiate)** : variante sans la forme FR, suite loading complète ×3 modèles. Résultat à double tranchant : `pos-03/09/15` **tiennent 9/9** (la forme FR ne porte pas les positifs FR) — mais la variante fuit **3 cellules négatives**, dont `neg-08`≡`neg-15` (release blocker) sur sonnet ET haiku. À n=1/cellule, causalité vs variance indécidable ; une variante sous le bar négatif de la cible ne se lit pas « tient ». **Forme FR conservée, finding clos en non-édit mesuré** ; ré-ouverture conditionnée à une ablation n≥3. Données : `gotchas-log.md` (entrée W5) + `docs/harness/2026-08-05-run4/ablation_matrix.json`.

## Findings contestés

**DIM-7-01** porte le seul bloc de preuve contradictoire du run (soulevé par le Grounder, jamais appliqué — sévérité maintenue WARNING) :

- *Pour le finding* : issue #327 d'anthropics/claude-plugins-official (la redondance de description est un défaut reconnu, 8 skills corrigés) ; platform.claude.com (~100 tok/skill toujours chargés ; « Concise is key »).
- *Contre* : docs.anthropic.com (« Check the description includes keywords users would naturally say » — pour un opérateur francophone, la forme FR EST le mot naturellement dit, donc une surface de déclenchement distincte, pas un synonyme) ; best-practices endorse les triggers explicites ; #327 s'auto-étiquette « Low priority — cosmetic » (sur une classe de redondance différente).

**L'adjudication appartient à Victor.** L'action que les deux camps soutiennent est la même : l'ablation avant toute édition.

### ADVISORY (17) — une ligne chacun

| # | Dim | Ancre | Constat → fix |
|---|---|---|---|
| 1 | D1 | `evals/loading.jsonl:8,30` | `neg-08`/`neg-15` byte-identiques : la barre négative compte une sonde deux fois → le déclarer dans `rubric.md:15` ou re-phraser `neg-15` |
| 2 | D1 | `evals/loading.jsonl:2,5,7,13` | 9/43 verdicts négatifs nomment des skills inexistants (`research`, `scrape` = commandes) : un pass certifie le silence, pas la propriété → une phrase à `rubric.md:7` |
| 3 | D1 | `evals/rubric.md:15` | 2 NO_VERDICT haiku rendent la barre brute ≥14/15 insatisfiable → la re-formuler en ratio sur verdicts mesurés |
| 4 | D2 | `SKILL.md:17-26` | ~150 tok de Trigger post-routage → retitrer « Post-load self-check », ne garder que la ligne négative `:26` |
| 5 | D2 | `SKILL.md:116,136,143,160` | Contrat des 5 artefacts énoncé 4× → replier `:160` en pointeur vers Output Format |
| 6 | D2 | `SKILL.md:53,81` | Chemins `~/.claude/` codés en dur sans `compatibility:` → déclarer la cible Claude Code en frontmatter |
| 7 | D2 | `solution-space.md:53` vs `SKILL.md:83` | « Web queries » vs « Tavily calls » : unités en désaccord, devenu load-bearing avec ≥3 requêtes GitHub → retitrer « Tavily queries » + exclure le GitHub-natif du budget |
| 8 | D3 | `CHANGELOG.md:18` | Load 7 199/7 500 (marge 4 %) au lendemain d'un dépassement de +33,8 % ; aucun garde CI → step `token_budget.py` dans `validate.yml` |
| 9 | D3 | `budget.json` | Index 171 vs cible 100 — hygiène seule → re-mesurer après les fixes D7 |
| 10 | D4 | `evals/e2e.jsonl:15` | Checks 1-3 d'`e2e-15` exécutables par rien (dont les 2 qui attraperaient W1/W5) → porter 1-2 dans la couche déterministe ; marquer 3 « live-run only » dans `rubric.md:35` |
| 11 | D4 | `sota-recall/ground-truth.json` (`wi`) | Aucun script ne lit le nouveau cas → assertion offline sur `expected_mechanism`, ou statut « manual replay » + cadence dans le README |
| 12 | D4 | `verify_gates.py:104` | Rule 7b valide la *forme* d'une chaîne, pas qu'un appel GitHub a eu lieu (sonde B : `topic:` typé dans une prose Tavily → PASS) → 4e bullet en Known limitations du CHANGELOG |
| 13 | D5 | `gotchas-log.md:24` vs `evals/rubric.md:42` | Le waiver de l'item 2 (négatif territorial) s'appuie sur une condition que l'item 1 seul porte → amender `rubric.md:42` avec « (if the feature adds a routing surface) » |
| 14 | D5 | `CHANGELOG.md:7,14,44,51` | Deux blocs `### Added` + deux `### Changed` sous `[Unreleased]` → fusionner à la promotion de version (pas une réécriture d'historique) |
| 15 | D6 | `conflict.json` | Jaccard 0,019 mesuré sur un corpus qui exclut les DEUX voisins nommés par l'auteur → consigner ; mesurer à la main contre `commands/research.md` si le risque compte |
| 16 | D6 | `SKILL.md:3` | La description défère à un sibling plugin absent de cette machine (0/133) → aucun changement requis ; préférer une classe décrite à un nom si révision |
| 17 | D7 | `SKILL.md:3` | Clause « runs autonomously… » = doc comportementale, no-op de routage (~25 tok) → supprimer, re-mesurer index + matrice, consigner |

## Coverage gaps (ce que ce run n'a PAS examiné)

- **D1** : corpus synthétique 28 entrées vs ~165 en prod (~6× plus facile) ; sibling plugin inexistant ici (`neg-08`/`neg-15` jamais satisfaisables comme décrits) ; framing « pick the most specific » du proxy ; la description mesurée est celle de `1f10507` (le commit sous revue ne la touche pas) ; aucune ablation de description.
- **D2** : `README.md` (40 KB) jamais lu (Analyst ni Critic) ; 12/16 fichiers de référence non Tax-testés ligne à ligne (~26k tok) ; `suggest-tooling/` hors périmètre ; aucun run live.
- **D3** : coût runtime réel Phase-0 ≈ 11 633 tok sur géométrie applicable (7 199 + 4 434 conditionnels, chiffre d'auteur) ; le tier files surestime ~23 % (19 915 tok de `.pyc`) ; `suggest-tooling/` non mesuré.
- **D4** : 28 fixtures (`progressive` + `e2e`) exécutées par rien — `[]` structurellement identique à un sans-faute, à lire NOT RUN ; `sycophancy` + `benchmark` inatteignables par `--suite` ; aucun run live `/deep-research` ; l'exemple CI (`eu-ai-act-2026`) est une géométrie `not-applicable` — **le step CI qui exécute le gate sur artefacts réels n'atteint jamais Rule 7b**.
- **D5** : historique d'édition des logs non audité au-delà de HEAD ; cadences de maintenance déclarées non vérifiées ; le résultat de run 39/39 vit en CHANGELOG, pas en gotchas-entry (une maison à choisir).
- **D6** : 133 skills plugin + 4 commandes hors instrument ; `suggest-tooling` non conflict-checké contre son parent ; intersection de phrases exactes non testée.
- **D7** : pas d'ablation (l'instrument n'existe pas — feature en file d'attente du harness) ; D7 lui-même UNCALIBRATED.

## Instructions de session de fix (agent autonome)

Ordre = racine d'abord ; les items 1-3 partagent un même commit logique.

1. `scripts/verify_gates.py` : scinder `GITHUB_TOPIC_FACET` / `GITHUB_NATIVE_QUERY`, Rule 7b → ≥3 slugs `topic:` distincts sur `live_queries` (open-source × swept/empty), violation dédiée <3 ; fixture #13 `probe-starband-only` + ligne dans `tests/check-solution-space.sh`.
2. `tests/fixtures/solution-space/valid.json` : 3e combinaison topic distincte ; assertion « golden ≥3 » dans le même script.
3. `references/solution-space.md:38` + `:21` + `references/anti-patterns.md:85` : alignement doctrine topic-facet (formes GitHub-natives en « use », `site:github.com` en « never », Instrument re-titré).
4. `SKILL.md:3` : brancher benchmark/citations dans la description (ou amender `pos-06.boundary`) ; re-run matrice ; consigner.
5. Ablation FR (`recherche approfondie sur X`) : re-run `--suite loading`, comparer `pos-03/09/15` ×3 modèles, consigner l'issue dans CHANGELOG — ferme DIM-7-01 quel que soit le résultat.
6. ADVISORY par lots : D2 (4-7), D3 (8), D4 (10-12), D5 (13-14), D1 (1-3), D7 (17). Chaque édition de `SKILL.md` → re-mesure budget + matrice avant commit.
7. Re-run `/skill-harness` après les fixes W1-W3 — la racine commune doit tomber sous vérification mécanique (fixture #13 verte).

## Recursion check

N/A — la cible n'est pas `skill-generator`.

## Défaut de rubric du harness (à relayer à skill-harness, pas à la cible)

Les deux WARNING les plus sévères (W1, W3) s'ancrent sur `scripts/verify_gates.py` et `tests/fixtures/` — **hors des inputs déclarés de D4** (« evals/ directory contents; rubric.md presence »). Le Critic le déclare lui-même (`findings_cited.md:241`) : **aucune dimension du rubric ne possède la cohérence gate ↔ golden ↔ doctrine** ; D4 n'est que « the least-bad home ». Conséquence pour le calibrateur : un humain appliquant les tiers littéralement note D4 = 10.0 — et les deux findings les plus graves du run n'ont alors **plus aucune maison dans le score** tout en restant vrais. C'est un défaut du rubric du harness (dimension manquante : cohérence interne de spec), pas de la cible ; il est consigné ici pour ne pas être absorbé en silence dans un écart de −3.0.

## Durabilité du dossier de preuve — décision Victor

L'entrée de calibration poussée (`CHANGELOG.md`, commit `38205fa`) référence ce `REVIEW.md` (gitignoré par convention du repo, `.gitignore:15`, précédent du run #2) et `.harness-staging/` (untracked). Le verdict est durable ; son substrat de preuve ne l'est pas. Trois options : (a) statu quo assumé — la convention du repo, le staging survit tant que le worktree vit ; (b) commit forcé de `REVIEW.md` contre le `.gitignore` ; (c) copie du dossier dans le vault. La décision appartient à Victor — le harness s'interdit de committer la cible, et le `.gitignore` est un choix délibéré de l'auteur qu'un rapport ne doit pas renverser unilatéralement.

## Entrée de calibration

**Run #4.** Trajectoire : 6.6 (FAIL) → 8.94 (PASS) → 6.84 (FAIL) → **7.61 (PASS)**. Le harness reste **UNCALIBRATED** (`calibration_runs: 0`, vérifié inchangé après ce run ; D7 doublement) : score à ne PAS prendre pour argent comptant — la revue humaine de ce run est due, et l'accord humain-vs-évaluateur est à consigner dans le `CHANGELOG.md` de la cible. L'écart déjà consigné (prédictions d'auteur d'avant-grade vs verdict) est un instrument **distinct** de la revue humaine : il mesure la calibration du producteur, pas celle de l'évaluateur.

Deux écarts délibérés au tier littéral, tous deux **à la baisse**, déclarés pour que la comparaison de calibration ait une cible fixe :
- **D3 : 7.5 gradé, 8.0 littéral** (l'index à 171 satisfait le disjonct tier-8 ; pénalisé pour le load à 96 % du hard cap, lendemain d'un breach, sans garde CI).
- **D4 : 7.0 gradé, 10.0 littéral** (tier-10 satisfait sur la *forme* ; gradé sur l'*exécutabilité* par directive du Strategist + 2 défauts mesurés que les tiers orientés-présence ne savent pas nommer).

Effet net : −0.55 (littéral : 8.16). **PASS sous les deux lectures.**

Note de processus (résolue post-run sur attestation du Critic) : le consult advisor du grading a été tenté **5×** — 4 overloaded, le **5e abouti après le premier dépôt de `findings.md` en staging**. Ses 4 corrections + 1 correctif arithmétique auto-détecté ont porté sur prose, comptages et attribution ; **aucun score de dimension n'a bougé** (vérifié position par position avant/après). L'advisor a vu scores ET prose et a recalculé l'overall indépendamment (« PASS stands »). Le §Process note des fichiers findings était exact à l'écriture et périmé d'une tentative ; il porte désormais une correction **en append** (trace d'audit préservée). Un second consult advisor pré-complétion, distinct (côté orchestrateur, sur le livrable final), a rendu 6 items — 1 blocker (levé : la dismissal check-17 re-vérifiée contre `critic-rubric.md:27` + `lint_skill.py:441-443`), 5 corrections de record toutes repliées dans ce rapport.
