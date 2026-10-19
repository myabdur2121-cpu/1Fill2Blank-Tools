# ইকোসিস্টেম মানচিত্র — কোন জিনিস কোথায় থাকে

এই দলিলের কাজ একটাই: নতুন কোনো AI (বা মানুষ) যেন ১০ মিনিটে বুঝে ফেলে
1Fill2Blank-এর Manim জগতে কোন repo, কোন folder, কোন ফাইলের দায়িত্ব কী।

## Repo গুলোর ভূমিকা

| Repo | ভূমিকা | এখানে যা থাকবে না |
|---|---|---|
| `1Fill2Blank-Tools` | পুনর্ব্যবহারযোগ্য skills, tools, templates, docs | কোনো একটি ভিডিওর project ফাইল, render করা মিডিয়া |
| `1Fill2Blank` | আসল project সমূহ (ভিডিওর কোড, config, manifest, নোট) | final MP4 (ওটা Releases-এ), venv/model |
| `manim-sandbox-setup` | শুধু runtime: ManimCE + slim LaTeX সেটআপ | project কোড, টুলস |
| `trush` | আর্কাইভ/সোর্স ভাণ্ডার: raw voice, পুরনো music library, আগের workspace snapshot | canonical চলমান কাজ (যদি না মালিক বলেন) |

নিয়ম: **যে জিনিস একাধিক project-এ কাজে লাগে → Tools। যা একটা ভিডিওর → Project।
যা চালানোর পরিবেশ → Setup। যা শুধু সংরক্ষণ → Archive।**

## Folder গুলোর ভূমিকা

| Folder | মানে |
|---|---|
| `skills/` | AI-এর জন্য লিখিত কাজের পদ্ধতি (Markdown)। কোড নয়, নির্দেশনা। |
| `tools/` | টেস্ট করা চালানো-যায় এমন script। নির্দেশনা নয়, যন্ত্র। |
| `templates/` | কপি করে শুরু করার খালি কাঠামো (config, manifest, নোট)। |
| `docs/bn/` | বাংলায় লম্বা ব্যাখ্যা ও মানচিত্র। |
| `scenes/` (project-এ) | Manim scene কোড। main ফাইল এখানে বা project root-এ। |
| `animations/` | পুনর্ব্যবহারযোগ্য animation primitive (যেমন bouncing grow)। |
| `brand/` | চ্যানেলের পরিচয়: logo, intro, brand music। |
| `scripts/` | voice script / build script (project অনুযায়ী)। |
| `audio/`, `narration/` | project-এর অডিও ডেটা ও বলার টেক্সট। |
| `videos/` বা `output/` | **শুধু final** ভিডিও। |
| `cache/`, `media/` | ফেলে দেওয়ার জিনিস: partial render, log, temp। Git-এ নয়। |

## Cache বনাম Archive — সবচেয়ে গুরুত্বপূর্ণ সতর্কতা

আগের workspace snapshot (`trush`-এর `whats up bro`)-তে `cache/`-এর ভেতরে
`mywork` নামের পুরো project আর্কাইভ রাখা ছিল। অর্থাৎ সেখানে cache মানে
সবসময় "ফেলে দেওয়ার জিনিস" ছিল না।

**তাই নিয়ম: folder-এর নাম দেখে কখনো মুছবে না।**
- মুছার আগে dry-run তালিকা বানাও: কী মুছতে চাও, কত জায়গা, কেন অপ্রয়োজনীয়।
- মালিকের স্পষ্ট অনুমতি ছাড়া delete/move নয়।
- ভবিষ্যতের নামকরণে পার্থক্য রাখো: `cache/` = disposable, `archive/` বা
  `mywork/` = সংরক্ষণযোগ্য পরীক্ষামূলক কাজ।

## একটা কাজের জীবনচক্র

```
আইডিয়া → lab ফাইলে পরীক্ষা → কম-মানের preview → মালিকের পছন্দ/সংশোধন
→ main ফাইলে যোগ (promote) → voice থাকলে sync (voice-to-manim skill)
→ draft render → QC → final render → PROGRESS/নোট আপডেট → Release
```

Graduation নিয়ম (আগের `mywork` সিস্টেম থেকে নেওয়া):
পরীক্ষামূলক কাজ আগে lab/mywork-এ থাকে; টেস্টে pass করলে তবেই canonical
repo-তে ওঠে, আর INDEX/নোটে status বদলায় (🚧 চলমান / ✅ pass / ❌ বাতিল)।

## নামকরণের ইঙ্গিত

- `*_scene.py` — সাধারণত main বা পূর্ণ scene ফাইল।
- `test_*.py`, `*_demo.py`, `*_variants.py`, `*_tests*.py` — lab/পরীক্ষা।
- `common.py` — এক project-এর shared helper ও style।
- `engine.py` / `BaseScene` — বহু পর্বে চলা কেন্দ্রীয় ইঞ্জিন।
- `partN.py` — ধারাবাহিক পর্ব; ভেতরে `s01, s02…` segment থাকতে পারে।
- `build_*.py`, `*_production.py` — **generated হতে পারে**; আগে দেখো ফাইলের
  মাথায় "হাতে সম্পাদনা কোরো না" জাতীয় সতর্কতা আছে কি না। থাকলে generator
  বা base ফাইল বদলাও, generated ফাইল নয়।
- `*_pauses.txt` — অডিওর নীরবতা বিশ্লেষণের আউটপুট (ডেটা, কোড নয়)।

## নতুন AI-এর পড়ার ক্রম

1. Tools repo-র `AGENTS.md`
2. এই মানচিত্র
3. কাজ অনুযায়ী Skill (`skills/…/SKILL.md`)
4. Project-এর `README.md` + `PROGRESS.md` (থাকলে)
5. Project-এর config/manifest
6. তবেই main scene ও lab ফাইল

পড়া শেষে মালিককে সংক্ষেপে জানাও: কোন ফাইল main, কোনটা lab, কোনটা cache,
আর তুমি কী করতে চাও। অনুমতি ছাড়া সম্পাদনা শুরু কোরো না।
