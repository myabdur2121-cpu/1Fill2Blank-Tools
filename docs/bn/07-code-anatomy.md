# কোড অ্যানাটমি — মালিকের কোড পড়ার ধরন

এই workspace-এর কোড "সাধারণ টেমপ্লেট" ধাঁচে লেখা নয়। মালিকের নিজস্ব সাজানো
ধরন আছে—সেটা না বুঝে সম্পাদনা করলে কাজ ভেঙে যাবে। মূলত **তিনটা composition
প্যাটার্ন** দেখা যায়। কোন ফাইল কোন প্যাটার্নে, সেটা আগে চেনো।

## প্যাটার্ন A — Builder + Director `construct()`

উদাহরণ: `scenes/factorial_scene.py` (`FactrioalScene`)।

- `hook_s1…hook_s7`, `make_player`, `make_field` জাতীয় method গুলো **animation
  চালায় না** (`self.play` নেই)। তারা Mobject বানিয়ে `self.players`,
  `self.blocks`, `self.tree`, `self.final_eq`-এর মতো **state** সাজিয়ে রাখে।
- `construct()` প্রথমে সব builder ডাকে, তারপর নিজে পরপর `play/wait` দিয়ে
  পুরো গল্পটা চালায়। **construct()-ই একমাত্র টাইমলাইন/পরিচালক।**
- অল্প কিছু micro-action method (`swap`, `highlight_path`,
  `play_choice_stage`) নিজে `play` করে, কিন্তু সেগুলোও construct থেকেই ডাকা হয়।
- Method-এর সংজ্ঞার ক্রম গল্পের ক্রম নয় (যেমন `hook_s5` সংজ্ঞায় `hook_s4`-এর
  আগে)—আসল ক্রম construct-এর ভেতরে।

**পড়তে হলে বের করো:** প্রতিটা builder কোন কোন `self.*` state বানায়, আর
construct-এর play-ক্রম।
**বদলাতে হলে:** object-এর চেহারা বদলালে builder-এ যাও; ঘটনার ক্রম/সময়
বদলালে construct-এ যাও।

## প্যাটার্ন B — Segment method + ছোট construct loop

উদাহরণ: Binomial প্রজেক্টের `part2.py`–`part4.py`।

- `construct()` খুব ছোট: `for i in range(1, 18): getattr(self, f"s{i:02d}")()`।
- আসল টাইমলাইন প্রতিটা `s01, s02…` method-এর ভেতরে।
- `common.py`-র `Narrated` mixin narration-এর সাথে sync করে: `clip(name)`
  অডিও বসায়, `at(t, …)` / `upto(t)` clip-আপেক্ষিক সেকেন্ডে animation সাজায়।
- Style (রং/ফন্ট/ধ্রুবক) `common.py`-তে এক জায়গায়।

**পড়তে হলে বের করো:** segment তালিকা, প্রতিটা segment কোন narration ফাইলের
সাথে বাঁধা, ভেতরের timestamp গুলো।
**বদলাতে হলে:** সংশ্লিষ্ট segment method বদলাও; timing কখনো construct-এ
টেনে আনবে না।

## প্যাটার্ন C — Engine/BaseScene + `body()`

উদাহরণ: Academy AI Teacher-এর engine উদাহরণসমূহ।

- কেন্দ্রীয় `BaseScene` (বা `P1`) নিজে `construct()` ও lifecycle সামলায়:
  পৃষ্ঠা পড়া, বোর্ড বসানো, reading bar, segment চক্র।
- প্রতিটা পাঠ/পর্ব শুধু subclass-এ `body()` override করে content দেয়।
- Helper primitive ইঞ্জিনে: `bn_wrap`, `qbox/qpanel`, `book_page`,
  `latex_paragraph`, `cluster_into_lines` ইত্যাদি।
- বইয়ের মূল লেখা LaTeX (flowing paragraph), বোর্ডের UI Manim `Text()`—
  এই hybrid বিভাজন ইচ্ছাকৃত সিদ্ধান্ত।

**পড়তে হলে বের করো:** base class-এর lifecycle, primitive গুলোর কাজ, কোন
subclass কোন পাঠ।
**বদলাতে হলে:** content বদলালে `body()`/ডেটা; আচরণ বদলালে ইঞ্জিন—কিন্তু
ইঞ্জিন বদলালে সব পর্ব প্রভাবিত হয়, তাই version ও পুনঃrender-এর হিসাব লাগবে।

## অন্যান্য চেনার চিহ্ন

- **এক ফাইলে অনেক scene class** (logo test/variant ফাইল): এগুলো lab-এর
  variant বাগান। প্রতিটা class একেকটা প্রস্তাব; সবগুলোই canonical নয়।
- **কপি হওয়া helper:** `FixedArrow`-এর মতো class একাধিক ফাইলে হুবহু থাকতে
  পারে। এটা ভবিষ্যতে shared primitive হওয়ার প্রার্থী—কিন্তু টেস্ট ছাড়া
  main ফাইলে refactor চাপাবে না।
- **ভাঙা/অসম্পূর্ণ খসড়া:** কিছু পুরনো ফাইলে syntax error থাকতে পারে
  (যেমন Missing Triangle-এর দুটো part)। এগুলো "চলে না" বলে রিপোর্ট করো,
  নিজে থেকে "ঠিক" করে ফেলবে না।
- **Generated ফাইল:** builder দিয়ে বানানো production scene সরাসরি সম্পাদনা
  নয়; base/config/generator বদলে আবার বানাও।

## কোনো project-এর CODE_ANATOMY লিখতে হলে

`templates/code_anatomy.template.md` ব্যবহার করো। মূল অংশগুলো:
entry point → কোন প্যাটার্ন → construct/segment/body মানচিত্র → state তালিকা →
ডেটা/asset → lab ফাইল → ভাঙা বা generated ফাইল → নিরাপদ সম্পাদনার জায়গা →
টেস্ট কমান্ড।
