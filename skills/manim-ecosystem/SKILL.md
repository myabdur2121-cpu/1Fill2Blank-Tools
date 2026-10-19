# Skill: manim-ecosystem (understand, organize, and extend Manim projects)

Version: see repo `VERSION`. Owner communication: Bangla (বাংলা) by default.
Companion docs (Bangla): `docs/bn/06-ecosystem-map.md`, `07-code-anatomy.md`,
`08-main-plus-lab-workflow.md`. Companion tools: `tools/analyze_manim_project.py`,
`tools/cache_report.py`, `tools/project_index.py`.

## Purpose

Let any future AI/human enter a 1Fill2Blank Manim project, understand how its
code is composed, and extend it **without breaking the owner's Main + Lab
style**: one canonical main file, experiments in lab files, approved pieces
promoted into main, disposable render material in cache, and every decision
written down for the next agent.

Use this skill when: onboarding to an unfamiliar project, reorganizing files,
adding/changing an animation, auditing storage/cache, or preparing a handoff.
For turning recorded voice into a synced video, use `voice-to-manim` — but
understand the base scene with this skill first.

## Inputs (gather before editing)

1. This repo's `START_HERE.md` + `AGENTS.md` (read order and hard rules).
2. The target project folder/repo and the owner's task in 2–3 lines.
3. Project memory, if present: `README.md`, `PROGRESS.md`, `DECISIONS.md`,
   `CODE_ANATOMY.md`, config/manifests.
4. `manim-sandbox-setup` repo if anything must be rendered.

## Outputs

- A reviewed `CODE_ANATOMY` (draft from the analyzer + human/AI judgement).
- Lab previews and, after approval, a minimal promotion into main.
- Updated project memory: `PROGRESS.md`, `DECISIONS.md`, anatomy if structure changed.
- Reports the owner asked for (index, cache dry-run) — never silent cleanups.
- Upstream Tool/Skill improvements only when generally reusable, with tests
  and a `CHANGELOG.md` entry (see `UPDATE_GUIDE.md`).

## Hard rules

- **Sector gates:** split work into sectors; finish one, report, then stop and
  wait for the owner's reply before the next sector.
- **Read before edit.** No editing until you can say: which file is main,
  which are lab, which are cache, and which composition pattern applies.
- **No delete/move/overwrite** without showing a list and getting approval.
  Cache work is dry-run only (`cache_report.py` never deletes).
- **Folder name ≠ disposable.** Old snapshots kept a whole archive under
  `cache/mywork`; treat code/docs/data inside cache as archive until proven otherwise.
- **Preserve the owner's pattern.** Do not refactor a main file into a generic
  style. Tools explain and guard the style; they do not replace it.
- **Generated files are not edited by hand** — change the generator/base/config.
- **Broken drafts are reported, not "fixed"** on your own initiative.
- No secrets in files/Git; push only on the owner's specific authorization.

## Workflow

### 0. Orient
Read `START_HERE.md` → `AGENTS.md` → this skill → the Bangla docs 06–08 as
needed → project memory. Confirm repo roles: Tools (reusable), Projects
(`1Fill2Blank`), Setup (runtime), Archive (`trush`).

### 1. Inventory — read-only first
Run the analyzers; treat their output as evidence, not truth:

```bash
python tools/analyze_manim_project.py <project> > CODE_ANATOMY.draft.md
python tools/project_index.py <projects-parent> > INDEX.draft.md   # collections
python tools/cache_report.py <workspace> > cache_report.md          # storage only
```

Then verify by reading key files yourself. Report back in a few lines:
main file/class, pattern, lab files, cache/archive risks, broken/generated
files, and your proposed sector plan.

### 2. Choose the edit surface by pattern
(Full guide: `docs/bn/07-code-anatomy.md`.)

| Pattern | Recognize by | Change visuals in | Change order/timing in |
|---|---|---|---|
| A: Builder + Director | `hook_*`/`make_*` set `self.*`, no `play`; long `construct()` plays everything | builder methods | `construct()` |
| B: Segment loop | tiny construct loop with `getattr(self, "s..")`; `s01…` methods hold timelines (+ narration `clip/at/upto`) | the segment method | the segment + narration map |
| C: Engine + `body()` | `BaseScene.construct()` calls `self.body()`; subclasses only override `body()` | `body()`/lesson data | engine only if behaviour must change for all parts |
| Direct / variants | one constructful scene, or many scene classes in one file | that scene | that scene (lab until promoted) |

Method definition order is **not** story order; the timeline is wherever the
pattern says it is.

### 3. Lab first for creative uncertainty
New visual ideas start in separate lab files (`test_*`, `*_demo`, `*_variants`)
— never directly in main. If the owner has no idea in mind, invent a proposal
in lab, render low quality (`-ql`), and show it. The owner picks, mixes, or
rejects. Record the choice (and the rejected options) in `DECISIONS.md`;
rejected lab files stay as evidence unless the owner says to remove them.

### 4. Promote into main
Integrate only the approved piece, in the main file's own pattern:
builder + construct insertion (A), a segment (B), or body/data (C).
Use the promotion checklist in `CHECKLIST.md`. If promotion copies a helper
(e.g. an arrow class) that already exists elsewhere, note it as a future
shared-primitive candidate — don't refactor main opportunistically.

### 5. Voice/timing work
Once visual beats are understood, switch to the `voice-to-manim` skill.
Timing is fixed through manifests/marks/pads, never by sprinkling arbitrary
`wait()` calls into a scene.

### 6. Render & QC
Draft-render only the affected range; inspect frames. A content mistake fixes
one segment/scene; a shared helper/engine bug is fixed centrally and all
affected parts are re-rendered. Finals follow the project workflow; final
MP4s go to GitHub Releases, not Git history.

### 7. Close the sector
Update `PROGRESS.md` (done / in progress / next + whose permission is needed),
`DECISIONS.md` for any choice, and standing owner instructions if new ones
were given. Report: files changed, commands/tests run, results. Then stop.

## Failure modes already learned (do not rediscover)

- `cache/` once contained the `mywork` archive → never bulk-delete by name.
- In Pattern A, hooks defined out of order (e.g. `hook_s5` before `hook_s4`)
  are normal; construct holds the real sequence.
- Example engine files may import a module name (`engine`) that differs from
  the snapshot filename — map intent, don't assume imports run as-is.
- Some old part files have syntax errors; analyzers must report, not crash.
- A file with many scene classes is a variant garden, not many canonical videos.
- Sandbox resets drop packages/caches → re-verify environment and file
  presence before rendering.
