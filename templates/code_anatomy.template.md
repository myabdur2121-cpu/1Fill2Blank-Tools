# CODE ANATOMY — <project name>

> এই ফাইল উত্তর দেয়: "এই project-এর কোড কীভাবে সাজানো, আর নিরাপদে
> বদলাতে হলে কোথায় হাত দিতে হয়?" প্যাটার্নের ব্যাখ্যা:
> Tools repo-র `docs/bn/07-code-anatomy.md`।

## এক নজরে
- Main ফাইল: `<path>` — Main class: `<ClassName>`
- প্যাটার্ন: A (Builder+Director) / B (Segment loop) / C (Engine+body) / সরাসরি
- মোট: <N ফাইল, ~M লাইন> — শেষ যাচাই: <YYYY-MM-DD>

## Entry point ও টাইমলাইন
- `construct()` কী করে (ক্রম অনুযায়ী):
  1. <builder/segment ডাক বা প্রথম অংশ>
  2. <…>

## Builder / Segment / Body মানচিত্র
| অংশ | কী বানায় বা চালায় | কোন `self.*` state | টীকা |
|---|---|---|---|
| `<name>` | <…> | `<self.x>` | <…> |

## ডেটা ও asset
- Narration/script: `<path>`
- Config/manifest: `<path>`
- ছবি/ফন্ট/music: `<path>`

## Lab ফাইল (canonical নয়)
- `<path>` — <কী পরীক্ষা হয়েছিল, সিদ্ধান্ত কী>

## Generated / ভাঙা ফাইল
- Generated: `<path>` — উৎস: `<generator/base>` (হাতে সম্পাদনা নয়)
- ভাঙা: `<path>` — <error + লাইন> (নিজে থেকে "ঠিক" করো না)

## নিরাপদ সম্পাদনার জায়গা
- চেহারা বদলাতে: <…>
- ক্রম/সময় বদলাতে: <…>
- লেখা/কণ্ঠ বদলাতে: <…>

## টেস্ট কমান্ড
```bash
<draft render / QC কমান্ড>
```
প্রত্যাশিত ফল: <…>
