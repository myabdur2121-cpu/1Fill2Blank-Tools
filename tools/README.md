# Tools — status map

এই ফোল্ডারের সব script config-চালিত; project-নির্দিষ্ট path/নাম code-এ hardcode থাকে না।
নিয়ম: কোনো tool পাল্টালে `CHANGELOG.md`-তে এন্ট্রি দিতে হবে এবং অন্তত একটা dry-run/উদাহরণ টেস্ট চালাতে হবে।

| Tool | Status | কাজ |
|---|---|---|
| `inventory_audio.py` | ✅ implemented (Step 3) | সব clip-এর ffprobe inventory JSON: duration, sample-rate, channels, codec |
| `transcribe_clips.py` | ✅ generic (Step 3) | clip-by-clip ASR (faster-whisper; FFmpeg দিয়ে 16 kHz mono decode)। `--dry-run` টেস্ট হয়েছে; পুরো ASR চালাতে ASR environment লাগে। |
| `prepare_voice_units.py` | ✅ implemented (Step 3) | decisions JSON থেকে cleaned `Mxx.wav` + portable `voice_units.json`; sustained-speech trim, ছোট handle, standard/raw_phone cleanup |
| `manim_sync.py` | ✅ existing | Manim scene-এ `mark()`/`pad()` helper |
| `compute_pads.py` | ✅ existing + handle-aware mode (Step 3) | পুরোনো duration mode অপরিবর্তিত; `--voice-units` দিলে speech-to-speech gap অনুযায়ী pad + report |
| `make_music.py` | ✅ existing | ঠিক নির্দিষ্ট দৈর্ঘ্যের background music তৈরি |
| `mix_voice_music.py` | ✅ existing | mark ধরে voice বসানো, sidechain ducking, loudnorm, final MP4 |
| `qc_video.py` | ✅ implemented (Step 3) | spec, full decode, LUFS/true-peak, long-silence, contact sheet, speech-gap audit; JSON report |
| `analyze_manim_project.py` | ✅ implemented (ecosystem Sector 3, local draft) | Manim project পড়ে CODE_ANATOMY খসড়া: ফাইল/scene তালিকা, Pattern A/B/C শনাক্ত, builder-state ও segment মানচিত্র, ভাঙা/generated ফাইল। শুধু পড়ে—কোড চালায় না। |
| `cache_report.py` | ✅ implemented (ecosystem Sector 3, local draft) | cache/media/temp-এর dry-run হিসাব: strong candidate / review / archive-like আলাদা করে মাপে। **কখনো কিছু মোছে না।** |
| `project_index.py` | ✅ implemented (ecosystem Sector 3, local draft) | project ফোল্ডারগুলোর এক-লাইনের INDEX খসড়া: status ও সারাংশ notes/README থেকে, main ফাইল অনুমানে। |

## মূল কমান্ডগুলো (own-voice workflow)

```bash
# 1) Clip inventory — filename বিশ্বাস না করে প্রমাণ সংগ্রহ
python tools/inventory_audio.py <voice-folder> --output inventory.json

# 2) প্রতিটি clip আলাদা করে ASR (take mapping-এর জন্য)
python tools/transcribe_clips.py <voice-folder> --language bn --output transcripts.json

# 3) Editorial decisions থেকে cleaned units + manifest
python tools/prepare_voice_units.py \
  --decisions voice_unit_decisions.json \
  --out-dir audio_clean --out-manifest timing/voice_units.json

# 4) Pass-1 marks থেকে handle-aware pads
python tools/compute_pads.py timing/marks_pass1.json audio_clean timing/pad.json \
  --plan project_config.json --voice-units timing/voice_units.json \
  --report timing/pad_report.json

# 5) Final QC
python tools/qc_video.py final.mp4 --config project_config.json \
  --marks-final timing/marks_final.json --voice-units timing/voice_units.json \
  --contact-sheet contact_sheet.jpg --output qc_report.json
```

Music ও mixing-এর কমান্ড আগের মতোই (`make_music.py`, `mix_voice_music.py`); বিস্তারিত এই repo-র root README ও `docs/bn/`-এ আছে।

## Ecosystem কমান্ড (নতুন project বোঝা ও সাজানো)

```bash
# কোনো Manim project-এর কোড-মানচিত্রের খসড়া (read-only)
python tools/analyze_manim_project.py <project-folder> > CODE_ANATOMY.draft.md

# Cache-এ কী আছে তার হিসাব — dry-run, কিছু মোছা হয় না
python tools/cache_report.py <workspace-folder> > cache_report.md

# Project ফোল্ডারগুলোর INDEX খসড়া (mywork ধাঁচে)
python tools/project_index.py <projects-folder> > INDEX.draft.md
```

প্যাটার্ন ও ওয়ার্কফ্লোর ব্যাখ্যা: `docs/bn/06-ecosystem-map.md`,
`07-code-anatomy.md`, `08-main-plus-lab-workflow.md`; নতুন পরিবেশে
ডাউনলোড/পুনর্গঠনের তালিকা: `09-downloads-and-rebuild.md`।
