# HANDOFF PROMPT — অন্য AI-কে যা পাঠাবেন

নতুন কোনো AI-এর কাছে গেলে **শুধু নিচের বাক্সটা কপি করে পাঠালেই হবে।**
আলাদা করে কোনো ফাইল পাঠাতে হবে না—সবকিছু repo গুলোর ভেতরেই সাজানো আছে।

```text
তুমি আমার 1Fill2Blank Manim ecosystem-এ কাজ করবে। আমার সাথে বাংলায় কথা বলবে
এবং প্রতি বড় ধাপে ছোট করে জানাবে কী করছ।

প্রথমে কিছুই বদলাবে না—শুধু পড়বে, এই ক্রমে:
1) Tools repo: https://github.com/myabdur2121-cpu/1Fill2Blank-Tools
   → START_HERE.md, তারপর AGENTS.md
2) কাজ অনুযায়ী Skill: skills/manim-ecosystem/SKILL.md
   (নিজের কণ্ঠের ভিডিও হলে skills/voice-to-manim/SKILL.md-ও)
3) UPDATE_GUIDE.md
4) Projects repo: https://github.com/myabdur2121-cpu/1Fill2Blank
   → সংশ্লিষ্ট project-এর README/PROGRESS/CODE_ANATOMY/config
5) render লাগলে setup: https://github.com/myabdur212121-afk/manim-sandbox-setup

পড়া শেষে সংক্ষেপে বলো: কোন ফাইল main, কোনটা lab, কোনটা cache/archive,
কোড কোন প্যাটার্নে সাজানো, আর তোমার sector অনুযায়ী পরিকল্পনা।
আমি permission না দিলে edit/delete/move/push—কিছুই করবে না।
কাজ sector ভাগ করে করবে; প্রতি sector শেষে রিপোর্ট দিয়ে আমার জবাবের জন্য থামবে।

আজকের কাজ: <এখানে ২-৩ লাইনে লিখুন>
```

## খেয়াল রাখবেন

- **পাঠাবেন:** ওপরের prompt + যে project-এ কাজ, সেই ফোল্ডারের লিংক (যদি
  নির্দিষ্ট থাকে)।
- **পাঠাবেন না:** token (push-এর দরকার হলে শুধু তখন, কাজ শেষে সাথে সাথে
  revoke), পুরো পুরনো snapshot, cache/মিডিয়া ফোল্ডার।
- অন্য AI যদি GitHub খুলতে না পারে, তাকে এই ফাইলগুলোর কপি দিলেই চলবে:
  `START_HERE.md`, `AGENTS.md`, সংশ্লিষ্ট `skills/.../SKILL.md`,
  `UPDATE_GUIDE.md`, আর project-এর `README/PROGRESS`।
- কাজের ধরন অনুযায়ী আরও তৈরি বার্তা:
  `skills/manim-ecosystem/PROMPTS.md` (বিশ্লেষণ, lab আইডিয়া, promote,
  cache হিসাব, সিস্টেম আপডেট)।
