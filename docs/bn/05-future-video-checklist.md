# পরের ভিডিওর checklist — আর সহকারীকে দেওয়ার তৈরি prompt

## কাজ শুরু করার আগে ঠিক করো

- [ ] ভিডিওর দৈর্ঘ্যের লক্ষ্য কত? (মনে রেখো: voice-এর আসল দৈর্ঘ্যই শেষ কথা)
- [ ] Voice নিজের রেকর্ড, নাকি তৈরি করা? ছেলে/মেয়ে কণ্ঠ? গতি কেমন?
- [ ] Script-এর কোন অংশে কথা নেই (logo, শুধু animation)?
- [ ] Music-এর মেজাজ: শান্ত piano-ই থাকবে, নাকি অন্য কিছু?
- [ ] Final quality: 1080p30 যথেষ্ট, নাকি 1080p60 চাই?

## ধাপ অনুযায়ী checklist

1. [ ] Script কে scene অনুযায়ী segment-এ ভাগ করা
       (`templates/narration_segments.json` copy করে ভরো)
2. [ ] Formula গুলো মুখে বলার ভাষায় বদলানো (যেমন `n!` → "এন Factorial")
3. [ ] `project_plan.json`-এ order আর voice segment ঠিক করা
4. [ ] Manim scene-এ প্রতিটি জায়গায় `mark()` ও শেষে `END`,
       প্রতিটি segment শেষে `pad()`
5. [ ] pad ছাড়া pass 1 (480p) → `marks_pass1.json`
6. [ ] প্রতিটি segment-এর voice clip তৈরি/রেকর্ড (`S01.mp3` …)
7. [ ] `compute_pads.py` চালিয়ে `pad.json`; ছক দেখে অস্বাভাবিক বড়
       pad থাকলে segment ভাগ করা বা pad-এর জায়গা সরানো
8. [ ] pad সহ pass 2 (1080p) → `marks_final.json` + silent video
9. [ ] `make_music.py` দিয়ে ঠিক video দৈর্ঘ্যের background
       (লাগলে intro/outro preset)
10. [ ] `mix_voice_music.py` দিয়ে final MP4 (overlap পরীক্ষা নিজে থেকেই হয়)
11. [ ] QC: পুরো decode, loudness (-15…-16 LUFS), লম্বা নীরবতা নেই,
        ৫–৮টা জায়গার frame চোখে দেখা
12. [ ] নিজে শুনে যাচাই: English শব্দের উচ্চারণ, music-এর জোর,
        segment-এর ভেতরের stage মিলেছে কিনা
13. [ ] সব script, timing JSON, voice clip, music ও নোট উদাহরণের
        মতো সাজিয়ে রাখা

## ১০–১২ মিনিটের ভিডিওর জন্য বাড়তি পরিকল্পনা

- Chapter ধরে music-এর মানচিত্র: intro-তে উপস্থিতি বেশি,
  গভীর derivation-এ সবচেয়ে হালকা, example-এ সামান্য গতি,
  recap-এ শুরুর melody ফেরত, outro-তে resolve।
- ছোট শ্বাসের ফাঁকে music যেন ঢেউয়ের মতো ওঠানামা না করে,
  সেজন্য duck release ও অধ্যায়ভিত্তিক হালকা volume সমন্বয়।
- Segment বেশি হলে voice তৈরির সীমা/খরচের দিকেও খেয়াল—
  কাছাকাছি ছোট অংশ জোড়া দেওয়া যেতে পারে, যদি sync মার্ক ক্ষতি না করে।

## সমস্যা হলে কোথায় দেখবে

| লক্ষণ | সম্ভাব্য কারণ / সমাধান |
|---|---|
| Mixer OVERLAP বলে থেমে গেছে | Voice তার segment-এর চেয়ে লম্বা → pad বাড়াও, segment ভাগ করো, বা voice ছোট করো |
| এক জায়গায় ছবি অনেকক্ষণ থেমে থাকে | ওই segment-এর pad বড় → pad টা segment-এর ভেতরের stage গুলোতে ভাগ করো |
| Music কথার ওপরে ওঠে | `--music-below-voice-db` বাড়াও বা `--duck-ratio` বাড়াও |
| Logo অংশে music প্রায় শোনাই যায় না | `--music-below-voice-db` কমাও |
| Manim marks ফাইল আসছে না | Scene-এ `sync_start()`/`mark()` আছে কিনা, আর path/env ঠিক আছে কিনা দেখো |
| সরাসরি আসল (original) Factorial script চলছে না | ওগুলোতে পুরোনো workspace-এর hardcoded path আছে; নতুন কাজে `tools/`-এর reusable রূপ ব্যবহার করো |

## পরের ভিডিওর জন্য তৈরি prompt (copy করে ব্যবহার করো)

```text
আমি মোবাইল ব্যবহার করি। আমার 1Fill2Blank-Tools package টা ব্যবহার করে
এই নতুন Manim ভিডিওর পুরো audio-video production করে দাও।

আগে package-এর README.md আর docs/bn/ ফাইলগুলো পড়বে। তারপর:
১) আমার script কে scene অনুযায়ী segment-এ ভাগ করবে; formula মুখে বলার
   ভাষায় বদলাবে।
২) ManimCE + slim LaTeX ব্যবহার করবে; CMU Serif আর Noto Serif Bengali
   font যাচাই করবে।
৩) দুই pass পদ্ধতিতে sync করবে: প্রথমে marks মেপে pad হিসাব, তারপর
   pad সহ final render। শুধু অনুমান করে timing বসাবে না।
৪) Music হবে tools/make_music.py দিয়ে তৈরি original track; কারও গান
   copy করবে না। Voice চলার সময় sidechain ducking থাকবে, logo বা
   ফাঁকা অংশে music ধীরে ধীরে ফিরে আসবে।
৫) শেষে loudness, overlap, silence আর কয়েকটা frame যাচাই করে
   সত্যিকারের ফলাফলসহ রিপোর্ট দেবে—যা পরীক্ষা করনি তা হয়েছে বলবে না।
৬) নতুন সব script, timing ফাইল, voice clip, music আর নোট
   examples/ এর Factorial উদাহরণের মতো করে সাজিয়ে রাখবে।

আমার কাছে GitHub token চাইবে না এবং আমি দিলেও নেবে না। GitHub access
লাগলে সাময়িক public repo, এখানে ফাইল upload, অথবা আমার নিজের
মোবাইল/Termux থেকে push করার পথ ব্যবহার করবে।
```
