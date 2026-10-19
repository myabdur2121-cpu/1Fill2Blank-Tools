# CHANGELOG

## 0.2.1 — 2026-10-19

- ডাউনলোড ও পুনর্গঠনের canonical চেকলিস্ট যোগ: `docs/bn/09-downloads-and-rebuild.md`
  (setup repo থেকে ManimCE+slim LaTeX, fonts, FFmpeg, core/ASR প্যাকেজ ও
  small মডেল, সোর্সের অবস্থান, এবং stems/render জাতীয় আবার-বানানোর জিনিস)।
  START_HERE, দুই Skill, tools README ও requirements থেকে লিংক দেওয়া হয়েছে।

## 0.2.0 — 2026-10-19

- Ecosystem সংগঠন (Sectors 2–4): আগের AI-এর workspace ও মালিকের Main + Lab
  কাজের ধরন বিশ্লেষণ করে সিস্টেমে রূপ দেওয়া হয়েছে—
  - মানচিত্র ও গাইড: `docs/bn/06-ecosystem-map.md`, `07-code-anatomy.md`
    (Pattern A/B/C), `08-main-plus-lab-workflow.md`
  - Templates: `progress`, `decisions`, `user_instructions`, `code_anatomy`
  - Tools: `analyze_manim_project.py`, `cache_report.py` (dry-run),
    `project_index.py` — পুরনো snapshot দিয়ে টেস্ট করা (প্যাটার্ন শনাক্ত ও
    ভাঙা-ফাইল রিপোর্ট মিলেছে)
  - নতুন Skill: `skills/manim-ecosystem/` (SKILL + CHECKLIST + PROMPTS)
  - প্রবেশপথ ও রক্ষণাবেক্ষণ: `START_HERE.md`, `HANDOFF_PROMPT.md`,
    `UPDATE_GUIDE.md`; `AGENTS.md` ও README-র পড়ার ক্রম হালনাগাদ

## 0.1.0-draft — 2026-10-19

- `voice-to-manim` skill-এর প্রথম খসড়া: `SKILL.md`, `DECISION_RULES.md`, `QC_CHECKLIST.md`, `PROMPTS.md`
- Factorial (owner's own voice) production থেকে শেখা নিয়ম সংকলন: duplicate-take selection,
  micro-unit split, speech-to-speech gap policy, handle-aware pads, QC gates
- আগের Tools package (music/mix/pads/sync) এই কাঠামোয় আনা হয়েছে
- Step 3 (একই তারিখ): generic tools তৈরি ও টেস্ট সম্পন্ন —
  `inventory_audio.py`, `transcribe_clips.py`, `prepare_voice_units.py`, `qc_video.py` নতুন;
  `compute_pads.py`-তে handle-aware `--voice-units` mode যোগ।
  Factorial ডেটা দিয়ে pad হিসাব আগের ফলাফলের সঙ্গে হুবহু মিলেছে; final MP4-তে QC PASS।
  (বিস্তারিত workspace draft-এর `STEP3_REPORT.md`-তে।)
- GitHub-এ প্রকাশিত: `myabdur2121-cpu/1Fill2Blank-Tools` (2026-10-19, PR #1 merged)
