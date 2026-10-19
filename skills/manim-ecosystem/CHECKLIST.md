# Checklists — manim-ecosystem

## Before any edit
- [ ] Read `START_HERE.md`, `AGENTS.md`, the relevant Skill, project memory.
- [ ] Ran `analyze_manim_project.py` (and read its draft critically).
- [ ] Can name: main file/class, lab files, cache vs archive, data/assets.
- [ ] Pattern identified (A / B / C / Direct) with evidence, not a guess.
- [ ] Broken or generated files noted; generated files will not be hand-edited.
- [ ] Told the owner the sector plan; editing only within the approved sector.

## Pattern identification (quick cues)
- [ ] **A?** Builders have `play=0` and set `self.*`; construct is long and
      calls builders first, then plays the story.
- [ ] **B?** construct loops via `getattr(self, f"s{i:02d}")`; segments use
      `clip/at/upto` against narration timestamps.
- [ ] **C?** A base scene's construct calls `self.body()`; subclasses override
      only `body()`; helpers live in an engine/common module.
- [ ] **Direct/variants?** Single construct timeline, or many scene classes
      in one file (= lab proposals until one is promoted).

## Lab experiment
- [ ] Separate lab file/class; name makes "not canonical" obvious.
- [ ] Low-quality preview rendered; finals/caches kept out of main paths.
- [ ] Owner saw it (all variants, if several).
- [ ] Decision recorded in `DECISIONS.md` (picked / mixed / rejected + why).

## Promotion into main
- [ ] Source lab file/class named; only the approved piece moves.
- [ ] Inserted following main's pattern (builder+construct / segment / body).
- [ ] New `self.*` state or assets listed; duplicated helpers noted.
- [ ] Voice/timing impact checked (if any → `voice-to-manim` manifests).
- [ ] Affected range draft-rendered and frame-checked against before/after.
- [ ] `CODE_ANATOMY` updated if structure changed.

## Cache / storage work
- [ ] Only `cache_report.py` (dry-run). No delete flag exists — keep it that way.
- [ ] `archive_like` items reviewed first; folder name alone decides nothing.
- [ ] Cleanup list shown to owner (paths + sizes + why disposable).
- [ ] Explicit owner approval before any delete/move, in a later sector.

## Sector closeout
- [ ] `PROGRESS.md`: done / running / next (+ permission needed from whom).
- [ ] `DECISIONS.md`: every choice with a reason and rejected alternative.
- [ ] New standing owner instructions saved (no secrets/personal data).
- [ ] Report sent: files changed, tests run, results. Then stop and wait.

## Upstream or project-local?
- [ ] Useful in ≥2 projects / clearly general → Tools repo + test + CHANGELOG.
- [ ] Specific to one video/topic → stays in that project (config/notes).
- [ ] Unsure → keep project-local, note it as an upstream candidate.
