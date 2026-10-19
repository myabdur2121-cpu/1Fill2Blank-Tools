# Example — Factorial (owner's own voice)

এটি `voice-to-manim` skill-এর reference উদাহরণ। ভারী media এখানে নেই;
আসল project ফাইল আছে Projects repo-তে: `1Fill2Blank/year2026/factorial/my_voice/`।

## এক নজরে ফল

- Final: 1920×1080, 30 fps, 04:09.6, নিজের কণ্ঠ + ducked background music
- Voice: 39টি enhanced + 1টি raw take থেকে বেছে 40টি micro-unit (M01…M40)
- QC: −15.22 LUFS, true peak ≈ −1.4 dBFS, full decode OK, লম্বা silence নেই

## এই উদাহরণ থেকে যা যা শেখা skill-এ ঢুকেছে

- Duplicate take: enhanced 9 (দুটো লাইন একসঙ্গে) বাদ → raw 10 + enhanced 11 আলাদা করে নেওয়া
- একই প্রশ্নের 3টি take (13/15/16) থেকে শেষের পরিষ্কার take (16)
- লম্বা recording (4, 18, 27) natural pause-এ দুই unit-এ split
- প্রশ্নের পরে ~0.95–1.05 s speech-gap; handle ছোট রাখায় mix overlap এড়ানো
- Pass-1 (no-pad) render থেকে marks মেপে handle-aware pad হিসাব

বিস্তারিত: project-এর `notes/PRODUCTION_NOTES_MY_VOICE_BN.md` ও `timing/` ফোল্ডার।
