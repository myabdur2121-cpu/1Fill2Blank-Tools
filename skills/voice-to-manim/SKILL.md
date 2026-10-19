# Skill: voice-to-manim (own recorded voice → synced Manim video)

Version: see repo `VERSION`. Language of narration in the reference project: Bengali.
Reference implementation: `1Fill2Blank` → `year2026/factorial/my_voice/` (Factorial, owner's own voice, v1).

## Purpose

Turn a set of separately recorded voice clips (enhanced and/or raw) plus an existing
ManimCE scene into a finished, tightly synced educational video — reproducibly,
so that any future AI/human can redo or revise it from the manifests alone.

## Inputs (gather before starting)

1. Script/storyboard (the intended spoken lines, in order).
2. Base Manim scene (unsynced animation is fine) in the Projects repo.
3. Voice clips folder (enhanced and/or raw). Filenames are NOT trusted as ordering.
4. Brand assets (logo scene, fonts) and output spec (default 1920×1080 @ 30 fps).
5. Music choice: generated preset (default) or a provided track.

## Outputs

- Final MP4 (GitHub Release asset), silent render (working artifact)
- `voice_units.json` (canonical take/split/gap decisions), `project_config.json`
- Timing artifacts: pass-1 marks, pads + pad report, final marks, sync plan
- Production notes (what was chosen and why) + QC results

## Workflow

### 0. Bootstrap & verify environment
Set up ManimCE + slim LaTeX via `manim-sandbox-setup`. Verify `manim`, `ffmpeg/ffprobe`,
LaTeX engine, `dvisvgm` versions and record them in the production notes.
Render the setup repo's smoke example if anything looks off. Fix setup here, not in the project.

### 1. Inventory the audio — trust nothing
- `ffprobe` every clip: duration, sample rate, channels. Save an inventory JSON.
- Note naming gaps, duplicates, and clips that exist in one set (raw/enhanced) but not the other.

### 2. Transcribe & map takes to script lines
- ASR each clip separately (low-RAM: faster-whisper **small**, language forced, beam 5, temperature 0;
  decode via FFmpeg to 16 kHz mono). ASR is evidence, not truth — correct the text against the script.
- Detect: duplicate takes of the same line, one recording covering several lines,
  several recordings covering one line, and lines whose only take is raw/unenhanced.
- Choose one canonical take per line. Record every rejected alternate + the reason in the manifest.
- Never concatenate by filename order.

### 3. Build voice micro-units (M01, M02, …)
- One unit = one spoken beat aligned to one visual beat. Split long recordings only at natural pauses.
- Trim leading/trailing silence with sustained-speech detection; keep small handles
  (reference: ~0.08 s lead, ~0.10 s tail) so onsets are never clipped.
- Light cleanup only: high-pass (~65 Hz), short fades; extra denoising only for a raw-only take.
- Write `voice_units.json`: id, source file, trim in/out, actual speech in/out, corrected text,
  visual cue, `gap_after_speech_s`, output file. This file is the single source of truth for narration.

### 4. Gap policy (pauses are designed, not accidental)
Defaults, measured between **actual speech** (not file edges) — override per unit in the manifest:
- After a question (`?`): ~0.9–1.1 s
- After a normal sentence: ~0.30–0.45 s
- Lead-in to a question / mid-thought join: ~0.18–0.25 s
- Section change / “let it sink in”: per manifest; music-only visual stretches (logo, path tracing) are allowed.

### 5. Production scene with marks & pads
- Do not edit the base scene into a one-off mess. Generate/derive a production scene that:
  - calls `mark("Mxx")` exactly where each unit must start, writing scene-time marks to JSON;
  - calls `pad("Mxx")` to wait the computed extra time for that unit.
- Anchor marks to visual events (object created, swap begins, label written), not to guessed seconds.

### 6. Two-pass timing
1. **Pass 1 (no pads, low res):** render to measure natural animation durations → `marks_pass1.json`.
   Inspect a contact sheet; fix anchor placement and any too-slow/fast animation now.
2. **Compute pads** (handle-aware): pad per unit so that, in the final timeline,
   next speech starts at its mark and the realised speech-to-speech gap matches the manifest.
3. **Pass 2 (final):** render silent video at full spec → `marks_final.json` + silent MP4.

### 7. Music & mix
- Generate/trim music to the exact final duration (reference preset: background, 72 BPM, seeded).
- Place each unit at its final mark; sidechain-duck music under speech; loudness-normalise.
- Reject file overlaps: if silent handles would overlap, tighten handles/manifest — never weaken the check.

### 8. QC (all must pass — see QC_CHECKLIST.md)
Streams/spec, full decode, loudness (≈ −14…−16 LUFS, true peak ≤ −1 dBTP), long-silence scan,
contact-sheet visual inspection, spot re-transcription of unit beginnings, final speech-gap audit.

### 9. Human review loop
Owner comments by **timestamp**. Apply changes in `voice_units.json` / `project_config.json`
(take, split, gap, anchor), recompute pads, re-render. Never hand-edit the final MP4.
Version the result (v1, v2, …) and update the production notes.

## Failure modes already learned (do not rediscover)

- Medium ASR model OOMs in ~2 GB sandboxes → use small.
- Clip-onset detection can trigger on clicks → use sustained-speech detection, then check beginnings by re-transcription.
- Wide silent handles cause “overlap” at mix time → design gaps between speech, keep handles tight.
- Sandbox resets may drop packages/caches/generated folders → re-verify tools and file presence after any reset.
- Editing the same file in parallel can race → sequential edits for the same file.
