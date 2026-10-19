# তৈরি Prompt — manim-ecosystem

মালিকের জন্য কপি-পেস্ট করা যায় এমন বার্তা। `<...>` জায়গাগুলো বদলে দিলেই হবে।
সবচেয়ে ছোট ও সাধারণ সংস্করণটা repo root-এর `HANDOFF_PROMPT.md`-তেও আছে।

## ১) নতুন AI-কে পুরো সিস্টেম বোঝানো

```text
তুমি আমার 1Fill2Blank Manim ecosystem-এ কাজ করবে। বাংলায় কথা বলবে।
প্রথমে কিছুই বদলাবে না—শুধু পড়বে, এই ক্রমে:
1) Tools repo-র START_HERE.md আর AGENTS.md
2. skills/manim-ecosystem/SKILL.md (+ দরকার হলে docs/bn/06, 07, 08)
3) কাজটা নিজের কণ্ঠের ভিডিও হলে skills/voice-to-manim/SKILL.md
4) UPDATE_GUIDE.md
5) Project repo-তে সংশ্লিষ্ট project-এর README/PROGRESS/CODE_ANATOMY
পড়া শেষে সংক্ষেপে বলো: কোন ফাইল main, কোনটা lab, কোনটা cache/archive,
কোন প্যাটার্নে কোড সাজানো, আর তোমার sector অনুযায়ী পরিকল্পনা।
আমি permission না দিলে edit/delete/push করবে না।
```

## ২) একটা project বিশ্লেষণ করানো (read-only)

```text
এই project ফোল্ডারটা বিশ্লেষণ করো: <link বা path>
tools/analyze_manim_project.py চালিয়ে খসড়া বানাও, তারপর নিজে মূল ফাইলগুলো
পড়ে যাচাই করো। কিছু বদলাবে না। রিপোর্টে থাকবে: main ফাইল/class, প্যাটার্ন
(A/B/C) ও প্রমাণ, lab ফাইল, ডেটা/asset, ভাঙা বা generated ফাইল, আর নিরাপদে
কোথায় সম্পাদনা করা যাবে। শেষে পরের sector-এর প্রস্তাব দিয়ে থামবে।
```

## ৩) Lab-এ নতুন আইডিয়া চাওয়া

```text
আমার মাথায় এই অংশটার animation আসছে না: <অংশের বর্ণনা>
main ফাইলে হাত দেবে না। lab ফাইলে তোমার মতো করে একটা (বা দুটো variant)
প্রস্তাব বানিয়ে কম মানে render করে দেখাও। আমি দেখে পছন্দ/মিশ্রণ/বাতিল করব,
তারপর সিদ্ধান্তটা DECISIONS-এ লিখবে।
```

## ৪) Lab থেকে main-এ তোলা (promote)

```text
lab-এর এই অংশটা চূড়ান্ত: <lab ফাইল/class>
এবার এটা main animation-এর সাথে যোগ করো—main-এর নিজের প্যাটার্ন মেনে
(builder/segment/body যেখানে মানায়)। শুধু অনুমোদিত অংশটুকুই নেবে।
যোগ করার পর প্রভাবিত অংশ draft render করে আগের সাথে মিলিয়ে দেখাবে,
আর PROGRESS/CODE_ANATOMY আপডেট করে sector রিপোর্ট দেবে।
```

## ৫) Cache/জায়গার হিসাব (মোছা ছাড়া)

```text
এই ফোল্ডারে জায়গা কতটা cache খাচ্ছে দেখো: <link বা path>
শুধু tools/cache_report.py দিয়ে dry-run রিপোর্ট দাও—কিছু মুছবে/সরাবে না।
archive-like জিনিস আলাদা করে সতর্ক করো। আমি তালিকা দেখে অনুমতি দিলে
তবেই পরের sector-এ cleanup হবে।
```

## ৬) সিস্টেম আপডেট করানো

```text
Tools সিস্টেমে এই উন্নতিটা করতে চাই: <বর্ণনা>
UPDATE_GUIDE.md মেনে চলবে: আগে বলো এটা Skill/Tool/Template/Doc কোন স্তরে
যাবে আর কেন, তারপর sector ভাগ করে local draft-এ কাজ করো, টেস্ট চালাও,
CHANGELOG-তে Unreleased এন্ট্রি দাও। GitHub push আমার আলাদা অনুমতি ছাড়া নয়।
```
