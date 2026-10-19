# Voice আর video কীভাবে sync হলো

সমস্যাটা সহজ ভাষায়: animation নিজের গতিতে চলে, voice নিজের গতিতে
বলে। দুটোকে জোর করে একসাথে বসালে হয় কথা শেষ হওয়ার আগেই দৃশ্য পাল্টে
যায়, নয় দৃশ্য শেষ হয়ে কথা চলতে থাকে। এখানে সমাধানটা *মাপা*, অনুমান নয়।

## ধারণা: mark আর pad

Manim scene-এর ভেতরে প্রতিটি বড় অংশের শুরুতে একটি করে **mark** বসানো:

- `self.mark("S03")` — এই মুহূর্তে scene time কত, তা `marks.json`-এ লিখে রাখে।
- `self.pad("S03")` — `pad.json`-এ ওই segment-এর জন্য যত সেকেন্ড আছে,
  ততক্ষণ শেষ দৃশ্যটা ধরে রাখে (অতিরিক্ত `wait`)।

Reusable রূপটা `tools/manim_sync.py`-তে `VoiceSyncMixin` হিসেবে আছে।
Factorial-এ একই পদ্ধতি production scene-এর ভেতরে বসানো হয়েছিল
(হুবহু কোড: `examples/factorial/production-scripts-original/make_production_scene.py`
এবং তৈরি হওয়া `examples/factorial/scene/factorial_production.py`)।

নতুন scene-এ ব্যবহারের ধরন:

```python
from manim import *
from manim_sync import VoiceSyncMixin   # tools folder টা PYTHONPATH-এ রাখো,
                                        # অথবা ফাইলটা scene-এর পাশে copy করো

class MyScene(VoiceSyncMixin, MovingCameraScene):
    pad_file   = "work/my-video/pad.json"
    marks_file = "work/my-video/marks.json"

    def construct(self):
        # ... সব mobject আগে বানিয়ে নাও ...

        self.sync_start("S01")
        # ... S01-এর animation ...
        self.pad("S01")
        self.mark("S02")
        # ... S02-এর animation ...
        self.pad("S02")
        self.mark("LOGO_MID")
        # ... logo (কথা নেই) ...
        self.mark("S03")
        # ... এভাবে শেষ পর্যন্ত; একদম শেষে self.mark("END") ...
```

খেয়াল করো: `project_plan.json`-এর `order` তালিকার প্রতিটি নাম ঠিক
একবার করে `mark()` হতে হবে, এবং শেষে `END` mark টা থাকতে হবে।

## দুই pass পদ্ধতি

### Pass 1 — মাপ নেওয়া
`pad.json` না থাকলে সব `pad()` শূন্য সেকেন্ড অপেক্ষা করে—অর্থাৎ
animation তার স্বাভাবিক দৈর্ঘ্যে চলে। নিচু quality-তে (480p) render
করলেই প্রতিটি segment-এর আসল দৈর্ঘ্য পাওয়া যায় `marks_pass1.json`-এ।

Factorial-এ pass 1 ছিল **02:48.7**—script-এ আগে থেকে লেখা 02:49
window-র সঙ্গে প্রায় হুবহু মিলে গিয়েছিল।

### Pad হিসাব
`tools/compute_pads.py` প্রতিটি segment-এর জন্য হিসাব করে:

```text
pad = max(0, voice-এর দৈর্ঘ্য + 0.45s নিরাপত্তা ফাঁক − animation-এর দৈর্ঘ্য)
```

```bash
python tools/compute_pads.py work/my-video/marks_pass1.json work/my-video/audio work/my-video/pad.json \
  --plan work/my-video/project_plan.json
```

### Pass 2 — আসল render
এবার `pad.json` থাকায় প্রতিটি অংশ ঠিক ততটুকু লম্বা হয়, যতটুকু তার
voice-এর দরকার। এই render-এর `marks_final.json`-ই mixer-এর কাছে
চূড়ান্ত সত্য: কোন clip কত সেকেন্ডে বসবে।

## Factorial-এর সংখ্যাগুলো

| Segment | Animation | Voice | Pad |
|---|---:|---:|---:|
| S01 সূত্রসমূহ | 11.00s | 9.64s | 0 |
| S02 "!" ও তালিকা | 20.47s | 21.16s | +1.14s |
| S03 Football পরিচিতি | 7.53s | 11.86s | +4.78s |
| S04 Swap ও প্রশ্ন | 16.47s | 20.19s | +4.18s |
| S05 তিন ব্লক | 21.60s | 25.00s | +3.85s |
| S06 Tree তৈরি | 18.27s | 18.91s | +1.10s |
| S07 ছয় পথ ও 3! | 19.33s | 37.46s | **+18.58s** |
| S08 সাধারণ n! | 31.20s | 42.27s | +11.52s |
| S09 সমাপনী | 0.00s | 7.39s | +7.84s |

মোট pad **+53.0s**; তাই final 02:48.7 নয়, **03:41.6**। বিকল্প ছিল
voice জোর করে দ্রুত করা—সেটা না করে দৃশ্যকে থামিয়ে রাখা হয়েছে।

একটা সূক্ষ্ম সিদ্ধান্ত: S07-এর বড় 18.6s hold টা equation সাজার *পরে*
নয়, *আগে* রাখা—যখন পর্দায় পূর্ণ tree আর ছয়টি বিন্যাস দেখা যাচ্ছে,
কারণ narration তখন ঠিক ওই ছয়টি বিন্যাসের কথাই বলছে। শিক্ষা:
**pad বসাতে হয় এমন জায়গায়, যেখানে থেমে থাকা দৃশ্যটা তখনকার
কথার বিষয়।**

## যাচাই

Mixer কাজ শুরুর আগেই overlap পরীক্ষা করে: কোনো clip যেন পরের
segment শুরুর পরে শেষ না হয়। Factorial-এ সব gap ধনাত্মক ছিল
(0.23s–1.36s; পুরো ছক `examples/factorial/timing/sync_plan.json`-এ)।

## সীমাবদ্ধতা — জানা জরুরি

এই sync **segment পর্যায়ের**, বাক্য পর্যায়ের নয়। একটি segment-এর
ভেতরে একাধিক stage থাকলে (যেমন তিনটি ব্লকে 3→2→1) কথা আর ছবি
কয়েক সেকেন্ড আগে-পরে হতে পারে। সেটা আরও নিখুঁত করতে চাইলে
segment আরও ছোট করে ভাগ করতে হয়, অথবা segment-এর ভেতরে stage
অনুযায়ী আলাদা pad বসাতে হয়। Factorial-এ S07-এ ঠিক এই কারণেই
hold টা সচেতনভাবে ভেতরে সরানো হয়েছিল।
