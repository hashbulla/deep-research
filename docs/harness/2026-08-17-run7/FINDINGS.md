# Run #7 — the 3-model measurement, and why the package must NOT be pushed

> Measured 2026-08-17, graded against `SCORING-POLICY.md` (pre-registered before the data existed).
> **Verdict: DO NOT PUSH.** `neg-16`, a fixture this repo's own rubric designates a release blocker,
> leaks to `deep-research` on sonnet in **7 of 18 live calls (~39 %)** under the harness's default
> router framing — and in **5 of 5** under a strict "only if clearly in scope" framing, which is what
> makes this a description defect rather than an instrument artifact. The n=1 matrix reported 16/16
> because it drew the favorable side of a coin. Victor's conditional go was conditional on this
> measurement; the condition failed, so pushing now needs a fresh decision from him.

## 1. What the n=1 matrix said

`run_evals.py --suite loading --models opus,sonnet,haiku --backend cli`, exit 0:

| Model | Positives | Negatives | NO_VERDICT | neg-07 | neg-16 | n=1 verdict |
|---|---|---|---|---|---|---|
| opus | 15/15 | 16/16 | 0 | `research` | `none` | PASS |
| sonnet | 15/15 | 16/16 | 0 | `research` | `none` | PASS |
| haiku | 15/15 | 16/16 | 0 | `research` | `superpowers:dispatching-parallel-agents` | PASS |

Integrity checks passed before it was read: the index carried exactly **1** `deep-research` entry
with the branch wording and no dead clause; **87** distinct cache files (29 prompts × 3 models, no
collision); the models diverged on **8/31** rows, so the columns are independent; and the opus column
replayed run #6 **byte-for-byte on all 31 rows**, confirming neither corpus nor fixtures had drifted.

Every one of those checks was sound. The matrix was still wrong about `neg-16`, because n=1 cannot
see a coin.

## 2. What n≥3 with the cache bypassed said

`repeat_blockers.py 3 opus,sonnet,haiku` — `router_query` direct, no cache, backend flock held:

| Fixture / model | rep1 | rep2 | rep3 | Reading |
|---|---|---|---|---|
| neg-07 / opus | `research` | `none` | `none` | unstable, **no leak** (both values pass) |
| neg-07 / sonnet | `research` | `research` | `research` | stable |
| neg-07 / haiku | `research` | `research` | `research` | stable |
| neg-16 / opus | `none` | `none` | `none` | stable |
| **neg-16 / sonnet** | **`deep-research`** | `none` | **`deep-research`** | **LEAK 2/3** |
| neg-16 / haiku | `research` | `research` | `research` | stable |

Had those repetitions gone through `run_evals.py` instead of around its cache, they would have
replayed the single stored reply three times and printed "stable". The cache key is
sha256(prompt + system + model); 31/31 opus keys were verified present before the run.

## 3. Two probes, two hypotheses, both refuted — and the second one inverted

The checkpoint warned that a negative leak here can be an artifact of the proxy rather than a routing
defect. **There are two distinct artifact mechanisms, and conflating them is easy** — the first draft
of this document did exactly that. They were tested separately, one variable each.

### 3a. Corpus hypothesis — refuted

`run_evals.py` indexes `DEFAULT_CORPUS = ~/.claude/skills` only, and the owner `neg-16` names,
`dispatching-parallel-agents`, is a **plugin** skill outside that tree. With the legitimate owner
withheld, `deep-research` is arguably the nearest match. `probe_owner.py 5 sonnet` — arm B is arm A
plus a symlink to the installed `superpowers/6.3.0/skills/dispatching-parallel-agents`:

| Arm | Owner in index? | neg-16 / sonnet, n=5, cache bypassed | Leaks |
|---|---|---|---|
| A | **No** | `none`, `none`, `none`, **`deep-research`**, **`deep-research`** | 2/5 |
| B | **Yes** | **`deep-research`**, `none`, **`deep-research`**, `none`, `none` | 2/5 |

**The leak occurs with the legitimate owner present.** That is the refutation, and it is solid. The
rate equality (2/5 vs 2/5) is noise at n=5 and is not the argument.

### 3b. Framing hypothesis — refuted, and it points the opposite way

This is a **different** mechanism, and §3a says nothing about it. Finding #6 of
`harness-loading-eval-via-subagents` concerns the router prompt's **framing**: `build_skill_index`
rule 3 says "if multiple skills could match, pick the most specific one", and for `synthese` that
framing was the *only* lever — hardening the description closed no leaks, while a strict framing
dropped them 5→2 with the description unchanged. `probe_owner.py` held the framing constant in both
arms, so it left this untested.

`probe_framing.py 5 sonnet` varies **only rule 3**, corpus held constant at 30 skills:

| Arm | Rule 3 | neg-16 / sonnet, n=5, cache bypassed | Leaks |
|---|---|---|---|
| DEFAULT | "pick the most specific one" | `none`, `none`, `none`, **`deep-research`**, `none` | 1/5 |
| **STRICT** | "only if clearly within its stated scope; if uncertain or merely grazing, answer none" | **`deep-research`** ×5 | **5/5** |

**A strict framing does not close this leak — it amplifies it, 1/5 → 5/5.** That is the inverse of
`synthese`'s signature, and it is the strongest evidence in this document. Asked point-blank "is this
prompt *clearly within* `deep-research`'s stated scope?", sonnet answers **yes, five times out of
five**. The description asserts territory over the fan-out/gist intent; a framing that makes the
model consult that scope claim more literally therefore increases firing rather than suppressing it.

**Generalisation worth keeping:** the strict-framing arm is a **diagnostic for description
overclaim**, not a leak-suppressor. Strict framing *reduces* firing when the description does not
claim the territory (`synthese`: 5→2) and *increases* it when the description does
(`deep-research`: 1→5). Direction of movement identifies which layer owns the defect.

### 3c. Pooled evidence

Sonnet on `neg-16`, all cache-bypassed, default framing: 2/3 (repeats) + 2/5 (owner absent) + 2/5
(owner present) + 1/5 (framing arm) = **7/18 ≈ 39 %**. Under strict framing: **5/5**.

The defect is **sonnet-specific**: opus returned `none` 3/3, haiku `research` 3/3 and
`superpowers:dispatching-parallel-agents` in the matrix — that last one being the exact owner
`neg-16`'s boundary names.

## 4. Consequence for the release bar

`evals/rubric.md:17`: "A single negative failure on `neg-07`, or on the `neg-08`→`neg-15`→`neg-16`
succession (territorial neighbors) is a release blocker **regardless of the aggregate**."

The aggregate is excellent — 15/15 positives on three models, and 15/16 negatives on sonnet even
when the leaking draw lands. It does not matter. **The blocker fired.** The package does not clear
its own bar on sonnet, and the 7 commits stay unpushed.

What survives untouched: the **positive column**. `deep-research` is in the index on every arm, and
15/15 on three models is valid evidence that the compressed description still fires on its own
territory — the D1 claim. Read it as a *regression* claim against run #6 (same corpus, like-for-like,
opus replays byte-for-byte); it is weaker as an absolute production claim, because the 146 plugin
skills and the `/research` command surface that genuinely compete for research prompts are all
absent from the arbitration.

## 5. Second, independent finding: the harness violates its own rubric's setup

This did not cause the leak — §3 settles that — but it is a real defect and it was found on the way.

`evals/rubric.md:7` specifies the eval condition: "present the prompt in a fresh session with this
skill **(and its territorial neighbors — the Tavily MCP tools, the user-scope `/research` command,
and `superpowers:dispatching-parallel-agents` for fan-out probes) available**". `rubric.md:9` states
the principle, learned from run #4's phantom sibling: "**A neighbor that does not exist cannot be a
test condition.**"

`run_evals.py` presents 29–30 skills from `~/.claude/skills`. Measured the same day: **146**
`SKILL.md` under `~/.claude/plugins`, **4** user-scope commands under `~/.claude/commands`. Reading
all 16 negative `boundary` fields by hand gives the honest taxonomy — an earlier pass counted
"10 of 16 contaminated", which conflated three different surfaces:

| Class | Rows | Broken test condition? |
|---|---|---|
| Owner is an **MCP tool** (`tavily_search`, `tavily_extract`, `tavily_skill`/`context7`, `tavily_map`) | `neg-01`, `-02`, `-03`, `-04`, `-06`, `-13`, `-14` (7) | **No.** A "which *skill* fires" question has no legitimate skill answer; `none` is correct and passes. |
| Owner is a **user-scope command** (`/scrape`, `/research`) | `neg-05`, `neg-07` (+ `neg-14` partly) | **No**, same structure. |
| Owner is an installed skill **present** in the index | `neg-10` (`linkedin-post`), `neg-11` (`diagnosing-bugs`) | No — properly measured, both pass. |
| Owner **does not exist at all** | `neg-12` (`deck-generator` — verified absent from `~/.claude`) | Phantom owner, same class as the `neg-08`/`neg-15` defect. Passed `none` everywhere, so harmless today, but it asserts against something unreachable. |
| Owner is an installed skill **missing** from the index | `neg-16` (`dispatching-parallel-agents`) | **Yes** — the only genuinely mis-conditioned row. Arm B now supplies it. |

Note the bias direction, which matters when quoting any of these numbers: an under-inclusive corpus is
**monotone** — removing competitors can only push probability mass *toward* `deep-research`. So the
negative rows that passed did so under conditions *harder* than production and hold a fortiori; the
positives were measured on easy mode. The ambient-knowledge replies (`research` on `neg-07` from all
three models, `scrape` on `neg-05`, `superpowers:dispatching-parallel-agents` on `neg-16` from haiku —
all names **absent from the list the model was given**) do not invalidate those passes; they show the
models reaching past the synthetic prompt, which is worth knowing on its own.

## 6. Third finding: the corpus drifted mid-measurement, and it silently voids the cache

Another session symlinked `excalidraw-models` into `~/.claude/skills` at **19:13:10**, between the
matrix run (finished ~19:07, 29 skills) and the A/B probe (started ~19:16, 30 skills). Consequences:

- `repeat_blockers.py` computes its index **once at startup**, so its 18 calls are internally
  consistent at 29 skills. The probe's arms are both at 30/31, so the A/B stays one-variable-clean;
  `excalidraw-models` is a diagramming skill and does not compete for the `neg-16` prompt.
- **The 87-entry response cache is now unreachable.** The cache key hashes the system prompt, which
  embeds every corpus description. Re-running run #7 tomorrow will miss all 87 entries and re-issue
  every call, including the opus baseline — silently, with no warning, and possibly with different
  numbers. Anyone expecting a replay must first restore the 29-skill corpus or accept a fresh
  measurement.
- Generalisation for the gotchas log: **the corpus is a live shared mutable input to this eval.** Any
  session installing a skill perturbs every in-flight and cached measurement. Pin or snapshot it
  before a graded run.

## 7. What is owed next (design decisions — Victor's call, not applied here)

1. **The `neg-16` leak is a description defect to fix, then re-measure at n≥5 per model — and this
   recommendation now rests on evidence, not on elimination.** Both artifact hypotheses were tested
   and refuted (§3a, §3b), and the strict-framing arm returns `deep-research` **5/5** when asked
   whether the prompt is clearly in scope. The description claims the fan-out/gist territory it is
   supposed to defer. Caveat that makes this a design decision rather than a patch: the description
   sits at **zero margin on both gates** (lines and tokens), so sharpening the boundary means
   relocating or trading budget, not appending a clause. Note also that finding #6 measured
   description hardening to be powerless for `synthese` — that prior does **not** transfer here,
   precisely because the framing arms move in opposite directions.
2. **Corpus union for the harness** (`--corpus` already exists): `~/.claude/skills` + plugin skill
   trees + a stub per user-scope command, still excluding the target's own installed copy or the
   shadowing hazard returns. Commands and MCP tools are different surfaces from skills; stubs
   approximate the real router, they do not reproduce it — say so wherever the number is quoted.
3. **`neg-12`'s phantom owner** (`deck-generator`) should be superseded the way `neg-16` superseded
   `neg-15`, not edited.
4. **n≥5, not n≥3, on release blockers.** A 40–50 % leak is invisible at n=1 and can still read
   "stable" at n=3 (opus did: 3/3 `none`). DIM-1-02 should be re-specified accordingly.

## Artifacts in this directory

| File | What it is |
|---|---|
| `SCORING-POLICY.md` | reading rules, pre-registered before any data existed |
| `loading_matrix_3models.json` | the n=1 matrix, 3 models × 31 fixtures |
| `GRADE.txt` | the matrix graded against the policy (all-PASS — the misleading result) |
| `repeat-blockers-n3.txt` | n≥3 on the blockers, cache bypassed — where the leak appeared |
| `probe-neg16-sonnet.txt` | the corpus A/B (§3a) — leak persists with the owner present |
| `probe-framing-sonnet.txt` | the framing A/B (§3b) — strict framing amplifies the leak 1/5 -> 5/5 |
| `grade.py`, `repeat_blockers.py`, `probe_owner.py`, `probe_framing.py` | the four instruments, kept runnable |
