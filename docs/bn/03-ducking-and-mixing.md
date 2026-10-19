# Voice এলে music নিজে থেকে কমে কীভাবে — ducking ও mixing

## তুমি যা শুনেছো, তার পেছনের কৌশল

ভিডিওতে music একটাই, একটানা। তবু logo-র সময় সেটা একটু সামনে শোনা
গেছে, কথা চলার সময় পেছনে। এটা হাতে volume ওঠানো-নামানো নয়—
এটা **sidechain ducking**:

```text
voice track ──┬────────────────────────────────→ final mix
              │
              └──(শুধু "কথা আছে কিনা" সংকেত)──┐
                                              ▼
music track ──→ volume ঠিক করা ──→ compressor ──→ final mix
                                   (voice পেলেই
                                    music নামিয়ে দেয়)
```

একজন sound engineer-এর স্বয়ংক্রিয় হাত ভাবতে পারো: কথা শুরু হলেই
সে music-এর knob নামায়, কথা থামলে আস্তে আস্তে আবার তোলে।

## Factorial-এ ব্যবহৃত হুবহু মান

সব `tools/mix_voice_music.py`-তে default হিসেবে রাখা আছে:

| ধাপ | মান | মানে |
|---|---|---|
| Voice high-pass | 70 Hz | অপ্রয়োজনীয় নিচু গুমগুম শব্দ কাটা |
| Music-এর প্রাথমিক স্তর | voice গড়ের **11 dB নিচে** | duck ছাড়া অবস্থাতেও music কথার ওপরে নয় |
| মাপা voice গড় | -23.5 dB | পুরো voice track-এর `volumedetect` mean |
| মাপা কাঁচা music গড় | -15.9 dB | মানে কাঁচা music আসলে voice-এর চেয়ে জোরে ছিল! |
| প্রয়োগ করা music gain | ×0.1175 (**-18.6 dB**) | (-23.5 − 11) লক্ষ্যে পৌঁছাতে |
| Sidechain threshold | 0.02 | এর ওপরে voice এলেই duck শুরু |
| Ratio | 6 | voice যত জোরে, music তত বেশি নামে |
| Attack | 150 ms | কথা শুরু হলে কত দ্রুত নামবে |
| Release | 850 ms | কথা থামলে কত ধীরে ফিরে উঠবে |
| Loudnorm | I=-15 LUFS, TP=-1.5, LRA=11 | YouTube-বান্ধব সামগ্রিক জোর |
| আউটপুট | AAC 192k, stereo, 48 kHz | video stream copy (আবার encode নয়) |

Release 850 ms বলেই দুই বাক্যের ছোট ফাঁকে music হঠাৎ লাফিয়ে ওঠে
না; কিন্তু logo-র মতো 10 সেকেন্ডের ফাঁকে সে পুরোপুরি নিজের স্তরে
ফিরে আসে। সেজন্যই logo অংশে music "বেড়ে গেছে" মনে হয়—আসলে সে
শুধু নিজের জায়গায় ফিরে এসেছে।

## Final ফাইলে মাপা ফল (Factorial)

- সমন্বিত loudness: **-15.8 LUFS**; true peak **-1.2 dBFS**
- কথা চলা অংশের গড়: প্রায় -18.5 dB
- শুধু music (logo) অংশের গড়: প্রায় -25…-27 dB
- পুরো ভিডিওতে -45 dB-এর নিচে 3 সেকেন্ডের বেশি নীরবতা নেই
  (music সব ফাঁক ভরে রাখে)

## নিজে যাচাই করার command

```bash
# Stream ও duration
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=codec_type,codec_name,width,height,channels final.mp4

# Loudness (শেষের Integrated loudness দেখো)
ffmpeg -i final.mp4 -af ebur128=peak=true -f null -

# লম্বা নীরবতা আছে কিনা
ffmpeg -i final.mp4 -af silencedetect=noise=-45dB:d=3 -f null -

# পুরো ফাইল ঠিকমতো পড়া যায় কিনা
ffmpeg -v error -i final.mp4 -f null - && echo DECODE_OK
```

## বদলাতে চাইলে কোন knob কোন দিকে

| চাওয়া | বদল |
|---|---|
| Music সামগ্রিকভাবে আরও জোরে/আস্তে | `--music-below-voice-db` কমাও/বাড়াও (default 11) |
| হাতে নির্দিষ্ট gain | `--music-gain-db -18` জাতীয় মান |
| কথা এলেই music আরও গভীরে নামুক | `--duck-ratio` বাড়াও (যেমন 8) |
| ফাঁকে music আরও ধীরে উঠুক | `--duck-release` বাড়াও (যেমন 1200) |
| ছোট music ফাইল পুরো ভিডিও জুড়ে ঘুরুক | `--loop-music` |
| Loudnorm ছাড়া mix | `--no-loudnorm` (সাধারণত দরকার নেই) |
