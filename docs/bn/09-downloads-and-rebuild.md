# ডাউনলোড ও পুনর্গঠন — নতুন পরিবেশে যা লাগবে

Workspace পরিষ্কার করা হলে বা sandbox reset হলে পরের AI/মানুষের প্রথম প্রশ্ন
হয়: “আবার কাজ শুরু করতে কী কী নামাতে হবে, আর কোনগুলো ডাউনলোড নয়—আবার
বানাতে হবে?” এই ডক সেই প্রশ্নের এক জায়গার উত্তর।

মূলনীতি আগের মতোই: **Tools repo নিজে Manim/LaTeX ইনস্টল করে না।** Runtime-এর
canonical জায়গা হলো আলাদা `manim-sandbox-setup` repo; কোনো নির্দিষ্ট
ভিডিওর হুবহু rebuild ক্রম থাকে সেই project-এর নিজের `REBUILD.md`-তে।
এই ডক শুধু মানচিত্র—কোনটা কোথা থেকে আসে, কখন লাগে।

## কিছুই ইনস্টল না করে যা করা যায়

- সব Skill/doc পড়া।
- Ecosystem টুলস তিনটা (`analyze_manim_project.py`, `cache_report.py`,
  `project_index.py`) — শুধু Python standard library ব্যবহার করে।
- `transcribe_clips.py --help` ও `--dry-run` — numpy/faster-whisper lazy
  import হয় বলে এগুলো ASR পরিবেশ ছাড়াই চলে; আসল transcription-এই কেবল
  প্যাকেজ ও মডেল লাগে।

## ডাউনলোডের তালিকা

| জিনিস | কোথা থেকে / কমান্ড | কখন লাগে | টীকা |
|---|---|---|---|
| Setup repo | `git clone https://github.com/myabdur212121-afk/manim-sandbox-setup.git` — persistent জায়গায় (Arena/E2B-তে `/home/user`-এর নিচে) | যেকোনো render-এর আগে | Public repo, token লাগে না। বারবার নতুন clone না করে একই checkout রাখো—font cache ওখানেই থাকে। |
| ManimCE + slim LaTeX | setup ফোল্ডার থেকে: `bash manimce.sh && bash latex_slim.sh` | ManimCE render + `Tex`/`MathTex` | আমাদের default এই জোড়া। Full TeX Live কয়েক GB—মালিক না বললে নয়। Sandbox reset-এর পর এই দুটো আবার চালাতে হয়; `bin/manim` wrapper দিয়েই render করো। |
| Fonts (CMU Serif + Noto Serif Bengali) | engine installer নিজেই `font.sh` ডাকে; প্রথমবার ডাউনলোড হয়ে `<workspace>/fonts/`-এ থাকে (~৫.২ MiB) | বাংলা/CMU টেক্সট | পরেরবার reuse হয়। `fonts/` মুছবে না, `git clean -fdx` নয়। যাচাই: `bash font.sh --check` |
| FFmpeg + ffprobe | সিস্টেমে থাকতে হবে (`ffmpeg -version`, `ffprobe -version` দিয়ে যাচাই) | audio inventory, ASR decode, pads, mix, QC | না থাকলে setup পরিবেশ/ডিস্ট্রো প্যাকেজ থেকে আনতে হবে; Tools নিজে ইনস্টল করে না। |
| Tools-এর core Python প্যাকেজ | `pip install -r $TOOLS/requirements.txt` (বর্তমানে `numpy`) | `make_music`, `prepare_voice_units`, ASR decode | বাকি বেশিরভাগ টুল stdlib + FFmpeg-ই যথেষ্ট। Global pip-এ না ঢেলে venv ব্যবহার করো। |
| ASR প্যাকেজ (optional) | আলাদা venv-এ `pip install faster-whisper` | শুধু আসল transcription | Generic টুল FFmpeg দিয়ে decode করে array পাঠায়, তাই **PyAV লাগে না**। |
| ASR মডেল | প্রথম আসল রানেই faster-whisper নিজে নামায় (cache বা `--model-dir`-এ) | transcription | Default **`small` + CPU int8**; ~২ GB sandbox-এ `medium` OOM হয়—চালাবে না। মডেল কয়েকশো MB-র অর্ডারের হতে পারে; ঠিক আকার মডেল/revision অনুযায়ী বদলায়। |
| Project ও সোর্স | Projects repo `1Fill2Blank` clone; voice/পুরনো music-এর সোর্স `trush` থেকে (project config/`REBUILD.md`-র পথ ধরে) | কোনো ভিডিও আবার বানাতে | শুধু তৈরি ভিডিও দরকার হলে GitHub **Release** থেকে final MP4 নামাও—সেটা সম্পাদনাযোগ্য সোর্সের বদলি নয়। |

### ASR পরিবেশ আবার বানানোর উদাহরণ

```bash
# কাজের ফোল্ডারে (নামটা উদাহরণ; venv Git-এ যাবে না)
python3 -m venv asr_env
./asr_env/bin/pip install -r $TOOLS/requirements.txt faster-whisper

# আগে dry-run (মডেল নামবে না), তারপর আসল রান (প্রথমবার মডেল নামবে)
./asr_env/bin/python $TOOLS/tools/transcribe_clips.py <voice-folder> --dry-run
./asr_env/bin/python $TOOLS/tools/transcribe_clips.py <voice-folder> \
  --language bn --model small --device cpu --compute-type int8 \
  --model-dir asr_models --output transcripts.json
```

 `--model-dir` না দিলে মডেল default cache-এ যাবে; দুটোই ঠিক, তবে রিপোর্টে
কোনটা ব্যবহার হয়েছে লিখে রাখো।

## ডাউনলোড নয় — আবার বানাতে হয়

| জিনিস | বানানোর পথ |
|---|---|
| Clean voice stems (`M01…M40` জাতীয়) | `prepare_voice_units.py` + project-এর decisions ফাইল + সোর্স voice (`--source-root`)। নাম ধরে জোড়া লাগানো নয়—Skill-এর take-mapping নিয়ম মানো। |
| Timing pads | Pass-1 (no-pad) render থেকে marks → `compute_pads.py` |
| Background music | `make_music.py` (preset/BPM/seed project config-তে)। কোনো sample/loop ডাউনলোড নেই। পুরনো তৈরি MP3 library ব্যবহার করলে সেটা `trush` থেকে আসে। |
| Silent/final render, Manim `media/` | setup-এর `bin/manim` দিয়ে render; factorial-ধাঁচের project-এ repo root `PYTHONPATH`-এ রাখতে হতে পারে—হুবহু কমান্ড project-এর `REBUILD.md`-তে। |
| Model/bytecode cache, partial video, log | বানানোই এদের কাজ; সোর্স হিসেবে কখনো নির্ভর কোরো না। |

উদাহরণ: Factorial (own voice) আবার বানানোর পুরো ক্রম আছে Projects repo-র
`year2026/factorial/my_voice/REBUILD.md`-তে। এখানে সেটা কপি করা হলো না—
project-নির্দিষ্ট ক্রম project-এই canonical থাকে।

## Reset/পরিষ্কারের পর চেকলিস্ট

- [ ] Repo গুলো আছে? না থাকলে শুধু যেটা নেই সেটা clone করো (Tools/Projects/Setup; সোর্স লাগলে `trush`)।
- [ ] Render লাগবে? `$SETUP/bin/manim --version` চলছে? না চললে setup ফোল্ডার থেকে `bash manimce.sh && bash latex_slim.sh` আবার চালাও (custom workspace হলে একই `MANIM_WORKSPACE` সব জায়গায়)।
- [ ] `bash font.sh --check` ঠিক আছে? LaTeX লাগলে `FontsAndMath` উদাহরণ render করে দেখো।
- [ ] `ffmpeg -version` ও `ffprobe -version` পাওয়া যাচ্ছে?
- [ ] ASR সত্যিই লাগবে? শুধু তখনই venv + faster-whisper; প্রথমে `--dry-run`, তারপর small/int8।
- [ ] সোর্স ফাইল গুনে মিলিয়েছ (`inventory_audio.py`)? ফাইলের নাম বিশ্বাস কোরো না।
- [ ] Generated জিনিস project-এর ক্রম ধরে আবার বানাচ্ছ—Release-এর final MP4 দিয়ে stem/render-এর ঘাটতি পূরণের চেষ্টা নয়।

## সময় নিয়ে বাস্তব ধারণা

ডাউনলোড নিজে সাধারণত বড় বাধা নয়; সময় যায় **ইনস্টল, ASR চালানো আর
render**-এ। Slim LaTeX-ই আমাদের পথ—Full TeX Live কয়েক GB ও অনেক ধীর।
আকার/সময়ের সংখ্যা পরিবেশভেদে বদলায়, তাই কাজের রিপোর্টে অনুমান না লিখে
যা যা যাচাই করলে (version, কমান্ড, ফল) তাই লিখে রাখো।

সবশেষে মনে রাখো: venv, model cache, generated WAV/MP4 আর Manim `media/`
**Git-এ যায় না**; final MP4 যায় Release-এ; আর token/secret কোনো ফাইলে
কখনোই নয়।
