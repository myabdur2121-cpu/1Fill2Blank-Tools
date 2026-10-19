# Decision rules — voice-to-manim

এই নিয়মগুলো Factorial (own voice) production থেকে শেখা। দ্বিধা হলে owner-কে timestampসহ জিজ্ঞেস করো; অনুমান করে final বানিয়ো না।

## 1. Take selection

- একই লাইনের একাধিক take থাকলে **শেষের দিকের পরিষ্কার take** সাধারণত ভালো, কিন্তু শুনে/ASR মিলিয়ে যাচাই করতে হবে।
- একটা recording যদি দুটো লাইন একসঙ্গে বলে, আর আলাদা আলাদা take-ও থাকে, তাহলে **আলাদা take** নাও — sync-এর স্বাধীনতা বেশি।
  - উদাহরণ (Factorial): enhanced 9 একাই দুটো লাইন বলেছিল; বাদ দিয়ে raw 10 + enhanced 11 নেওয়া হয়েছে।
- শুধু raw take থাকলে সেটাই নাও, আলাদা cleanup পথে (high-pass + gentle denoise + fade), আর manifest-এ চিহ্নিত রাখো।
- বাদ দেওয়া প্রতিটি take `excluded_alternate_takes`-এ কারণসহ লিখতে হবে। নীরবে কিছু বাদ যাবে না।
- ASR কোনো লাইন বুঝতে না পারলে script + ক্রম + visual cue মিলিয়ে সিদ্ধান্ত নাও, আর notes-এ “শুনে যাচাই বাকি” বলে flag করো।

## 2. Splitting & trimming

- Split শুধু natural pause-এ। শব্দের মাঝখানে কখনোই নয়।
- Onset খুঁজতে click-ভিত্তিক threshold নয়, **sustained-speech** detection ব্যবহার করো।
- Handle ছোট রাখো (reference: lead ~0.08 s, tail ~0.10 s)। বড় handle mix-এর সময় overlap তৈরি করে।
- Trim-এর পর প্রতিটি unit-এর **শুরুটা re-transcribe** করে যাচাই করো, যাতে প্রথম ধ্বনি কেটে না যায়।

## 3. Gaps (actual speech-to-speech)

| পরিস্থিতি | Default gap |
|---|---:|
| প্রশ্নের (`?`) পরে | 0.90–1.10 s |
| সাধারণ বাক্যের পরে | 0.30–0.45 s |
| প্রশ্নের ভূমিকা (“তাহলে প্রশ্ন হলো:”) | 0.18–0.25 s |
| একই চিন্তার জোড়া অংশ | 0.18–0.30 s |
| Section বদল / ভাবার সময় | manifest অনুযায়ী, music চলবে |
| Logo/outro/visual-only অংশ | music-only, আলাদা mark (যেমন `LOGO_MID`, `OUTRO`) |

- Gap সবসময় **কথা শেষ → পরের কথা শুরু** হিসেবে মাপা হবে, ফাইলের কিনারা ধরে নয়।
- Animation যদি নিজে থেকেই লম্বা হয়, সেখানে বাড়তি pad দরকার নেই; দীর্ঘ visual-only অংশে music যেন নীরব না থাকে।

## 4. Anchoring (mark কোথায় বসবে)

- Mark বসবে visual ঘটনার গোড়ায়: object আসা, swap শুরু, label লেখা, equation assemble শুরু।
- কোনো unit চলাকালীন একাধিক visual stage থাকলে stage বদলের জায়গায় ভিতরের pad/mark ভাগ করে দাও।
- Pass-1 contact sheet দেখে anchor ভুল জায়গায় থাকলে আগে anchor ঠিক করো, তারপর pad হিসাব।

## 5. কখন থামবে / জিজ্ঞেস করবে

- Script-এর কোনো লাইনের take পাওয়া যাচ্ছে না, বা দুটো take-এর অর্থ আলাদা।
- Repo/link inaccessible (private/404)।
- QC gate fail (loudness, overlap, লম্বা silence, কাটা onset)।
- Delete/move/overwrite বা push লাগবে — এগুলোতে সবসময় আগে অনুমতি।
