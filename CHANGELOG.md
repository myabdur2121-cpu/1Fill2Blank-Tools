# CHANGELOG

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
- এখনো GitHub-এ push হয়নি — local draft
