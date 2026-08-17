# Addendum to run #6 — the D1 evidence survived a corpus-shadowing hazard, by accident

> Written after the report, during the pre-completion review. It does **not** change any score.
> It records *why* the D1 evidence is valid, because the reason is not the mechanism you would
> expect — and the next run may not be as lucky.

## The hazard

The loading matrix graded a **git worktree** (`~/.cache/claude-worktrees/AI-372-v1x-dettes`,
new description) while the router's synthetic index is built from the **installed corpus**
(`~/.claude/skills`), which contains `deep-research` as a **symlink to the main checkout** — i.e.
to the *old* description, dead-sibling clause included.

If both had entered the index, the 15/15 positive column would have measured "an index containing
both descriptions routes correctly", not "the new description routes correctly". The negative
column would have been unaffected (a leak is a verdict string, independent of which description
produced it), but the positive claim — the one that matters for a compression — would have been
void.

## Why it did not happen

Two guards exist in `build_skill_index` (`skill-generator/scripts/run_evals.py`). Measured
2026-08-17:

| Guard | Line | Fired? |
|---|---|---|
| Path identity — `peer_dir.resolve() == target_skill_path.resolve()` | ~220 | **No.** The worktree resolves to `~/.cache/claude-worktrees/AI-372-v1x-dettes`, the peer symlink to `~/second-brain/20-engineering/skills/deep-research`. Different paths, so the guard is inert whenever the target is a worktree, a copy, or a fork. |
| Name dedup — `not any(e[0] == name for e in entries)` | ~225 | **Yes.** The target is appended *first* (~211), so the peer carrying the old description is dropped. |

Verified empirically rather than argued:

```
entries named 'deep-research' in the index : 1
index contains the dead 'plugin-namespaced deep-research sibling' clause : False
index contains the new '(use /research —' wording : True
```

**So the D1 evidence stands.** The 15/15 measured the branch's description.

## What to carry forward

The protection came from **insertion order plus name dedup**, not from the guard written for this
purpose. Reverse the insertion order and the router would silently read the *installed* skill's
description while the report claimed to grade the branch — with no error, no warning, and a
plausible-looking matrix. That is the same failure class as run #6's own oracle defect
(`b175c5f`): a wrong value raises no suspicion.

Two concrete precautions for run #7 and any future worktree grade:

1. **Assert the index before trusting the matrix.** One line: count entries matching the target's
   frontmatter `name` and grep the index for a string unique to the branch's description. Cheap,
   and it converts an accident into a check.
2. **Prefer a corpus that excludes the installed copy** when grading anything other than the
   canonical install — build a symlink farm of the real peers minus the target's own name. The
   house rule already prescribes corpus control for territorial fixtures; this extends it to
   self-shadowing.

**Generalisation worth keeping:** when the object under test is *also* installed in the
environment that measures it, the measurement can silently read the installed copy. Enumerate
everything derived from a path — cache namespace, folder name, corpus membership, lint of the name
— because each one becomes a false signal the moment the graded artifact is not the installed one.
