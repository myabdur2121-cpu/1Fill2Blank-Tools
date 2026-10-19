# বাংলা ডক সূচি — কোনটা canonical, কোনটা background, কোনটা legacy

নতুন AI/পাঠকের জন্য এই সূচি বলে দেয় কোন ডক বর্তমান নির্দেশ, আর কোনটা
শুধু পেছনের ব্যাখ্যা বা ইতিহাস। দ্বন্দ্ব হলে সবসময় জিতবে:
`START_HERE.md` → `AGENTS.md` → সংশ্লিষ্ট `SKILL.md` → project-এর
`REBUILD.md`/config। এই ফোল্ডারের ডকগুলো তার ব্যাখ্যা ও মানচিত্র।

| ডক | Status | কাজ / নোট |
|---|---|---|
| `01-music-system.md` | Background | Generated music কীভাবে তৈরি হয় (preset/কাঠামো)। বর্তমান কমান্ড tools README ও Skill-এ। |
| `02-voice-video-sync.md` | Background | Mark/pad ধারণার ব্যাখ্যা। Own-voice কাজের canonical workflow `voice-to-manim` Skill-এ। |
| `03-ducking-and-mixing.md` | Background | Ducking/mixing-এর কৌশল ও Factorial-এ মাপা মান। বর্তমান target project config ও QC-তে। |
| `04-mobile-github-upload.md` | **Legacy / Deprecated** | প্রাথমিক ZIP/Termux আপলোড পর্বের লেখা; উল্লেখিত `mobile/termux_push.sh` বর্তমান repo-তে নেই। **অনুসরণ করবে না**—বর্তমান publish পথ START_HERE/UPDATE_GUIDE অনুযায়ী branch → PR। |
| `05-future-video-checklist.md` | Background | আগের checklist ও prompt-ধারণা। বর্তমান তৈরি prompt Skill ফোল্ডারগুলোর `PROMPTS.md`-তে। |
| `06-ecosystem-map.md` | **Canonical** | কোন repo/folder-এর দায়িত্ব কী; cache বনাম archive। |
| `07-code-anatomy.md` | **Canonical** | কোডের Pattern A/B/C ও নিরাপদ সম্পাদনার জায়গা। |
| `08-main-plus-lab-workflow.md` | **Canonical** | মালিকের Main + Lab কাজের নিয়ম। |
| `09-downloads-and-rebuild.md` | **Canonical** | নতুন পরিবেশে কী নামাতে হবে আর কী আবার বানাতে হয়। |

নিয়ম: নতুন ডক যোগ হলে এই সূচিতে এক লাইন যোগ করো। কোনো ডক অচল হয়ে গেলে
মুছে না ফেলে প্রথমে এখানে **Legacy/Deprecated** চিহ্ন দিয়ে বদলি পথটা দেখাও
(UPDATE_GUIDE-এর deprecation নিয়ম অনুযায়ী)।
