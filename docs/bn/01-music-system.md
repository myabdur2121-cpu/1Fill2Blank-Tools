# Music কীভাবে তৈরি হলো

## মূল সিদ্ধান্ত

3Blue1Brown-এর কোনো আসল গান ব্যবহার করা হয়নি—ওগুলো অন্যের copyrighted
কাজ। নেওয়া হয়েছে শুধু *ধরনটা*: ধীর, শান্ত, চিন্তাশীল piano, মাঝে
অনেক ফাঁকা জায়গা, কোনো drum বা উত্তেজক উপাদান নেই—যাতে গণিতের
ব্যাখ্যার সঙ্গে music লড়াই না করে।

সব সুর Python দিয়ে note অনুযায়ী বানানো (`tools/make_music.py`)।
কোনো sample, loop pack বা download করা audio নেই।

## সুরের কাঠামো

- **Tempo:** 72 BPM; এক bar = 4 beat = প্রায় 3.33 সেকেন্ড
- **Chord loop (8 bar):**
  Am(add9) → Fmaj7 → Cmaj7 → G6 → Am(add9) → Fmaj9-ধরনের → Em7 → G
- **তিনটি layer:**
  1. **Bass** — প্রতিটি bar-এর root note, খুব নরম
  2. **Pad** — পুরো bar জুড়ে ধরে থাকা হালকা chord
  3. **Piano** — chord-এর note একে একে (arpeggio), তার ওপর প্রতি
     দ্বিতীয় bar-এ অল্প একটু melody
- **Piano-র শব্দ:** শুধু মূল সুর নয়; তার সঙ্গে 2×, 3×, 4×... frequency-র
  ক্রমশ ক্ষীণ harmonic যোগ করা, এবং প্রতিটি note দ্রুত মিলিয়ে যায়
  (exponential decay)—এতে আসল piano তারের মতো চরিত্র আসে।
- **মানুষের ছোঁয়া:** প্রতিটি note-এর সময়ে ±0.02 সেকেন্ড এবং জোরে
  সামান্য এলোমেলো বদল (`--seed`, Factorial-এ 7)। একই seed মানেই
  প্রতিবার হুবহু একই ফল।
- **ঘরের অনুভূতি:** 0.11, 0.23, 0.39 ও 0.57 সেকেন্ড দেরিতে চারটি
  ক্রমশ ক্ষীণ প্রতিধ্বনি—সাধারণ reverb-এর সহজ বিকল্প।
- **শেষ ছোঁয়া:** শুরুতে 2.5s fade-in, শেষে 5s fade-out, peak 0.62-তে
  normalize। আউটপুট 44.1 kHz stereo WAV (পরে চাইলে MP3)।

## Preset গুলো

| Preset | কাজ | বিশেষত্ব |
|---|---|---|
| `background` | পুরো ভিডিওর নিচে | Factorial-এ ব্যবহৃত হুবহু আচরণ |
| `intro` | 5–10 সেকেন্ডের শুরু | দ্রুত fade-in, প্রথম 4 chord, আগেভাগে melody |
| `outro` | শেষের logo/সমাপনী | শেষ bar Cmaj7-তে resolve, লম্বা fade-out |

```bash
python tools/make_music.py 660 bg_11min.wav                 # background
python tools/make_music.py 8   intro.wav --preset intro
python tools/make_music.py 12  outro.wav --preset outro
python tools/make_music.py 60  alt.wav   --seed 21          # অন্য সংস্করণ
python tools/make_music.py 60  slow.wav  --bpm 64           # আরও ধীর
```

WAV বড় হয় (প্রতি মিনিটে প্রায় 10 MB); সংরক্ষণের জন্য MP3 করো:

```bash
ffmpeg -i bg_11min.wav -codec:a libmp3lame -b:a 256k bg_11min.mp3
```

## ১০–১২ মিনিটের ভিডিওতে কী করব — সত্যি কথাটা

বর্তমান generator ১০–১২ মিনিটের track বানাতে পারে, কিন্তু সে একই
8-bar পরিবার ঘুরিয়ে বাজায়—অত লম্বা সময়ে হুবহু একই গড়ন একঘেয়ে
লাগতে পারে। তাই লম্বা ভিডিওতে পরিকল্পনাটা এমন হবে:

- একই key/tempo/yন্ত্র রেখে chapter অনুযায়ী ৪–৫টি সংযুক্ত অংশ:
  intro-তে উপস্থিতি বেশি, গভীর derivation-এ সবচেয়ে হালকা,
  example-এ সামান্য বেশি গতি, recap-এ শুরুর melody ফিরিয়ে আনা,
  outro-তে resolve।
- অংশ বদল হবে scene বদলের মুহূর্তে (marks ধরে), বাক্যের মাঝখানে নয়।
- Ducking পুরো ভিডিও জুড়েই চলবে; শুধু ছোট শ্বাসের ফাঁকে যেন music
  ঢেউয়ের মতো ওঠানামা না করে সেদিকে খেয়াল রাখতে হবে।

অর্থাৎ এই ফাইলের সুর-ব্যবস্থাটাই ভিত্তি; লম্বা ভিডিওতে তার ওপর
chapter অনুযায়ী সাজানোটা যোগ হবে।

## সীমাবদ্ধতা

- এটি আসল piano recording নয়; খুব ভালো headphone-এ মন দিয়ে শুনলে
  synthetic চরিত্র ধরা পড়তে পারে। Voice-এর নিচে background হিসেবে
  সেটাই যথেষ্ট বলে যাচাই হয়েছে।
- `--only` দিয়ে stem বানালে প্রতিটি layer আলাদা পাওয়া যায়, তবে
  মূল mix-এর ভারসাম্য রাখতে stem-এর বেলায় `--peak 0` ব্যবহার করো;
  না হলে প্রতিটি stem আলাদাভাবে normalize হয়ে অনুপাত বদলে যাবে।
