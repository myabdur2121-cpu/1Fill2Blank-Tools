# QC checklist — voice-to-manim

সব ঘরে টিক না পড়লে ভিডিও “final” বলা যাবে না। ফলাফল production notes-এ লিখতে হবে।

## Audio / sync
- [ ] প্রতিটি unit-এর শুরু re-transcribe করে যাচাই: প্রথম ধ্বনি কাটেনি
- [ ] কোনো file overlap নেই; একমাত্র ব্যতিক্রম silent-handle ছোঁয়া হলেও speech gap audit-এ তা ব্যাখ্যা আছে
- [ ] Final speech-gap audit তৈরি; প্রশ্নের পরের gap policy অনুযায়ী (~0.9–1.1 s)
- [ ] 3 s-এর বেশি সম্পূর্ণ silence (< −45 dB) কোথাও নেই (visual-only অংশে music চলছে)
- [ ] Loudness প্রায় −14…−16 LUFS integrated; true peak ≤ −1 dBTP

## Video
- [ ] Stream spec ঠিক: 1920×1080, 30 fps, H.264 + AAC (বা project config অনুযায়ী)
- [ ] পুরো ফাইল decode করে কোনো error নেই
- [ ] Contact sheet দেখা হয়েছে: opening, মূল visual stages, equation, logo/outro ঠিক আছে
- [ ] Duration marks_final-এর `END`-এর সঙ্গে মেলে

## Reproducibility
- [ ] `voice_units.json` ও `project_config.json` আপডেট; বাদ দেওয়া take কারণসহ আছে
- [ ] Pass-1 marks, pads + pad report, final marks, sync plan সেভ আছে
- [ ] Production notes: environment versions, take/split/gap সিদ্ধান্ত, music settings, QC ফল, জানা সীমাবদ্ধতা
- [ ] কোনো secret/token কোনো ফাইলে নেই; commit তালিকায় venv/cache/generated media নেই

## Human review
- [ ] Owner preview দেখেছেন; correction থাকলে timestamp অনুযায়ী manifest বদলে re-render হয়েছে
- [ ] Version নম্বর বেড়েছে (v1 → v2) এবং notes-এ বদলের ইতিহাস আছে
