# 1Fill2Blank-Tools

Reusable tools and AI skills for 1Fill2Blank math videos (ManimCE).

এই repo-র কাজ একটাই: একবার শেখা production প্রসেসকে এমনভাবে গুছিয়ে রাখা,
যাতে পরের ভিডিওতে মানুষ বা AI — কেউই শুরু থেকে আবিষ্কার না করে।

## দুই মিনিটে শুরু

- **মানুষ হলে:** এই README → তারপর `skills/voice-to-manim/SKILL.md`
- **AI agent হলে:** আগে [`AGENTS.md`](AGENTS.md) পড়ো — সেখানে পড়ার ক্রম, নিয়ম আর থামার জায়গা বলা আছে।

## এই repo-তে যা আছে

| অংশ | জায়গা | ভূমিকা |
|---|---|---|
| Skill (মস্তিষ্ক) | `skills/voice-to-manim/` | নিজের রেকর্ড করা split voice থেকে sync করা Manim ভিডিও বানানোর পুরো workflow, সিদ্ধান্তের নিয়ম, QC checklist, তৈরি prompt |
| Tools (হাত) | `tools/` | Config-চালিত Python script: audio inventory, ASR, voice-unit preparation, pad হিসাব, music তৈরি, mixing, QC |
| Templates | `templates/` | নতুন project-এর জন্য JSON schema + example config |
| Setup | আলাদা repo: `manim-sandbox-setup` | ManimCE + slim LaTeX + FFmpeg + fonts সেটআপ। এখানে duplicate করা হয়নি। |

## যেসব জিনিস এই repo-তে থাকবে না

- কোনো নির্দিষ্ট ভিডিওর raw voice, final MP4, বা project-নির্দিষ্ট সিদ্ধান্ত
  (সেগুলো Projects repo `1Fill2Blank`-এ থাকে)
- Virtual environment, model cache, generated WAV/MP4 (recipe থেকে আবার তৈরি হয়)
- কোনো token/secret — কখনোই নয়

## মূল নীতি

1. **Tools generic, সিদ্ধান্ত config-এ।** Project-নির্দিষ্ট কিছু tool-এর code-এ hardcode হবে না।
2. **Skill versioned।** প্রতিটি project তার `project_config.json`-এ কোন skill version ব্যবহার করেছে তা pin করে রাখে।
3. **সাধারণ উন্নতি upstream-এ।** কোনো project-এ নতুন সাধারণ কৌশল পেলে সেটা এখানে তুলে version বাড়াতে হয়; project-নির্দিষ্ট টুইক project-এই থাকে।

## Version

দেখুন `VERSION` ও `CHANGELOG.md`।
