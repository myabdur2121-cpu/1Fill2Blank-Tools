# START HERE — নতুন হলে এখান থেকে

মালিক যদি শুধু এই repo-র লিংকটাই পাঠিয়ে থাকেন, তাহলে এই ফাইলটাই তোমার দরজা।
পুরো 1Fill2Blank Manim ecosystem বোঝার ক্রম এখানে দেওয়া আছে।

## তুমি কে?

| কে | কোথা থেকে শুরু |
|---|---|
| **AI agent** | এই ফাইল → [`AGENTS.md`](AGENTS.md) → কাজ অনুযায়ী Skill → project-এর নোট |
| **মানুষ/মালিক** | [`README.md`](README.md) → অন্য AI-কে পাঠাতে [`HANDOFF_PROMPT.md`](HANDOFF_PROMPT.md) |
| **ভবিষ্যৎ আপডেটকারী** | [`UPDATE_GUIDE.md`](UPDATE_GUIDE.md) → তারপর যে স্তর বদলাবে সেই অংশ |

## AI-এর পড়ার ক্রম (লাফ দেবে না)

1. এই `START_HERE.md`
2. [`AGENTS.md`](AGENTS.md) — কঠোর নিয়ম ও থামার জায়গা
3. কাজ অনুযায়ী Skill:
   - Project বোঝা/সাজানো/animation যোগ করা → [`skills/manim-ecosystem/SKILL.md`](skills/manim-ecosystem/SKILL.md)
   - নিজের রেকর্ড করা কণ্ঠ দিয়ে sync ভিডিও → [`skills/voice-to-manim/SKILL.md`](skills/voice-to-manim/SKILL.md)
4. পটভূমির মানচিত্র (বাংলা): [`docs/bn/06-ecosystem-map.md`](docs/bn/06-ecosystem-map.md),
   [`07-code-anatomy.md`](docs/bn/07-code-anatomy.md),
   [`08-main-plus-lab-workflow.md`](docs/bn/08-main-plus-lab-workflow.md)
5. [`UPDATE_GUIDE.md`](UPDATE_GUIDE.md) — সিস্টেম বদলাতে হলে
6. Projects repo `1Fill2Blank`-এ সংশ্লিষ্ট project-এর
   `README` / `PROGRESS` / `CODE_ANATOMY` / config
7. তারপরেই কেবল নির্দিষ্ট tool বা scene ফাইল

## সম্পর্কিত repo

- **এই repo (`1Fill2Blank-Tools`)** — পুনর্ব্যবহারযোগ্য skills/tools/templates/docs
- **`1Fill2Blank`** — আসল project সমূহ; final MP4 থাকে Releases-এ
- **`manim-sandbox-setup`** — শুধু runtime (ManimCE + slim LaTeX)
- **`trush`** — আর্কাইভ/সোর্স (raw voice, পুরনো music, আগের workspace snapshot)

## সোনালি নিয়ম (সংক্ষেপে)

- মালিকের সাথে **বাংলায়** কথা বলো; প্রতি বড় ধাপে ছোট progress update দাও।
- কাজ **sector**-এ ভাগ করো: এক sector শেষে রিপোর্ট দিয়ে থামো, মালিকের
  জবাবের পর পরেরটা।
- **আগে পড়ে বোঝো, পরে সম্পাদনা।** কোনটা main, কোনটা lab, কোনটা
  cache/archive—না বলতে পারলে হাত দেবে না।
- Folder-এর নাম দেখে কিছু **মুছবে না**; cache-এর ভেতরেও আর্কাইভ থাকতে পারে।
- মালিকের **Main + Lab** ধরন বজায় রাখো: পরীক্ষা lab-এ, চূড়ান্ত অংশ main-এ।
- Final ভিডিও Git-এ নয়, **Release**-এ। Token/secret কোনো ফাইলে **কখনোই** নয়।

## কাজ শুরুর আগে নিজেকে পরীক্ষা করো

এই ৫টা প্রশ্নের উত্তর না জানলে তুমি প্রস্তুত নও:

1. এই কাজে কোন Skill প্রযোজ্য?
2. Project-এর main ফাইল/class কোনটা, কোন প্যাটার্নে (A/B/C) সাজানো?
3. Lab ফাইল কোনগুলো, আর cache বলতে এখানে আসলে কী?
4. আগের সিদ্ধান্তগুলো কোথায় লেখা আছে (`PROGRESS`/`DECISIONS`)?
5. এই sector-এ ঠিক কী করবে, আর শেষে মালিককে কী দেখাবে?
