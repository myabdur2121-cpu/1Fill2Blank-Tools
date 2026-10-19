# AGENTS.md — instructions for AI agents

You are working with the 1Fill2Blank reusable tools/skills repository.
Follow this file before doing anything else.

## Read order (do not skip)

1. This `AGENTS.md`
2. `skills/voice-to-manim/SKILL.md` (canonical workflow)
3. `skills/voice-to-manim/DECISION_RULES.md` and `QC_CHECKLIST.md`
4. The target project's `README.md` and `project_config.json`
5. Only then look at individual tools/scenes.

## Communication with the owner

- Reply in Bangla (বাংলা) by default unless the owner asks otherwise.
- Give a short progress update at every major step: ✅ done / 🔄 running / ⏭️ next.
  The owner once stopped a run because silent work looked stuck — never work silently for long.
- Explain the plan before long or hard-to-reverse work. Report errors honestly; never invent success.

## Hard rules

- **No delete/move/overwrite** of existing user files without explicit approval.
- **No secrets in files or Git.** Never write a token into any file, remote URL, doc, or commit.
  Push only when the owner authorizes that specific push, and tell the owner to revoke the token right after.
- **Do not commit** virtualenvs, model caches, generated WAV/MP4, Manim `media/`, or duplicate renders.
  Final videos go to GitHub Releases, not Git history.
- If a linked repo is private/404/unreachable, **stop and report** — do not guess its contents or keep retrying.
- Never concatenate voice clips by filename order. Takes must be mapped by listening/ASR + script (see SKILL.md).
- Project-specific decisions belong in the project's `project_config.json` / `voice_units.json`,
  never hard-coded inside reusable tools.

## Environment

- Engine: **ManimCE** + **slim LaTeX**, set up via the separate `manim-sandbox-setup` repository.
  Read that repo's `AGENTS.md` for setup rules; do not duplicate installers here.
- After any sandbox reset, re-verify versions (manim, ffmpeg, latex, dvisvgm) before rendering.
- In low-RAM sandboxes (~2 GB), use faster-whisper **small** (medium will OOM). Decode audio with FFmpeg to 16 kHz mono for ASR.

## Versioning

- The skill is versioned (`VERSION`, `CHANGELOG.md`). Every project pins the skill name + version in `project_config.json`.
- A generally useful improvement found during a project must be upstreamed here with a CHANGELOG entry;
  a project-only tweak stays in that project's notes.

## Definition of done for a video

All items in `QC_CHECKLIST.md` pass, production notes are written, and the owner has reviewed the preview
(corrections are given by timestamp and applied via manifest/config, then re-rendered).
