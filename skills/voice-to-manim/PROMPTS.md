# তৈরি Prompt — ভবিষ্যতের AI-কে দেওয়ার জন্য

নতুন ভিডিওর সময় নিচের prompt কপি করে লিংকগুলো বসিয়ে দিলেই হবে।

## নতুন ভিডিও শুরু করার Prompt

```text
তুমি আমার personal assistant হিসেবে কাজ করবে। বাংলায় কথা বলবে এবং প্রতিটি বড় ধাপে ছোট progress update দেবে।

প্রথমে এই ক্রমে পড়ো:
1) Tools repo: <1Fill2Blank-Tools লিংক> — এর AGENTS.md, তারপর skills/voice-to-manim/SKILL.md, DECISION_RULES.md, QC_CHECKLIST.md
2) Project repo: <1Fill2Blank লিংক> — সংশ্লিষ্ট project-এর README.md ও project_config.json
3) Setup দরকার হলে Tools README থেকে manim-sandbox-setup-এর নির্দেশ follow করো (ManimCE + slim LaTeX)।

আমার নতুন voice clips এখানে: <voice folder/repo লিংক>
Script/scene এখানে: <project folder লিংক>

নিয়ম:
- প্রথমে শুধু inventory + plan দাও; আমি approve করলে কাজ শুরু করবে।
- Filename order-এ voice জোড়া দেবে না; SKILL.md অনুযায়ী take map করবে।
- প্রশ্নের (?) পরে ছোট pauseসহ SKILL-এর gap policy follow করবে।
- কোনো delete/move/push আমার অনুমতি ছাড়া করবে না। Token এখন দেব না; push-এর সময় হলে জানাব।
- শেষে QC checklist-এর সব ফলসহ ভিডিওটা আমার সামনে খুলে দেবে। আমি timestamp ধরে correction বললে manifest বদলে আবার render করবে।
```

## শুধু Review/Correction-এর Prompt

```text
আগের ভিডিওটার project folder পড়ো (README + project_config + voice_units)।
আমার correction: <timestamp — কী বদলাতে হবে>
শুধু সংশ্লিষ্ট unit-এর take/gap/anchor বদলাও, pads আবার হিসাব করো, re-render করে QC ফলসহ নতুন version দেখাও।
```

## শুধু Push-এর Prompt

```text
PUSH_PLAN.md অনুযায়ী push করো। আগে কোন token কোন account/repo-র তা read-only যাচাই করো, fresh clone করো, branch-এ push করো (সরাসরি main নয়)।
Final MP4 যাবে GitHub Release-এ। শেষে commit hash ও লিংক দেবে; তারপর আমি token revoke করব।
```
