# মোবাইল থেকে GitHub-এ তোলা (PC ছাড়া, token share না করে)

> **⚠️ Deprecated (legacy) — এই নথি আর অনুসরণ করবে না।**
> এটি প্রাথমিক ZIP/Termux আপলোড পর্বের লেখা। এখানে উল্লেখিত
> `mobile/termux_push.sh` বর্তমান repo-তে নেই এবং `tools/audio-video`
> পথটাও এখনকার repo-বিভাজনের সঙ্গে মেলে না। বর্তমান পথ হলো:
> repo-র root-এর `START_HERE.md` ও `HANDOFF_PROMPT.md` দিয়ে শুরু করে
> `UPDATE_GUIDE.md` অনুযায়ী branch → PR → merge। ডকগুলোর status সূচি:
> এই ফোল্ডারের `README.md`। নিচের লেখা শুধু ইতিহাস হিসেবে রাখা হলো।

## আগে মূল কথাটা

এই package ব্যবহারের জন্য **কারও হাতে token দিতে হয় না**। তোমার সামনে
তিনটি বাস্তব পথ আছে; উদ্দেশ্য অনুযায়ী বেছে নাও:

| উদ্দেশ্য | সেরা পথ |
|---|---|
| শুধু পরের ভিডিওতে এই chat/workspace-এ কাজ করা | কিছুই করতে হবে না—folder টা এখানেই থাকল |
| স্থায়ীভাবে আলাদা GitHub repo হিসেবে রাখা | **Termux script** (এই নথির পথ ক) |
| বিদ্যমান `1Fill2Blank` repo-র ভেতরে `tools/` folder হিসেবে রাখা | Termux দিয়ে clone + copy (পথ খ) |
| শুধু একটা backup ফাইল রেখে দেওয়া | ZIP টা ফোনে/Drive-এ রাখা, বা GitHub Release-এ attach করা (পথ গ) |

> একটা ভুল ধারণা ভাঙা জরুরি: **ZIP ফাইল GitHub repo-তে upload করলে
> GitHub সেটা নিজে থেকে খুলে folder বানিয়ে দেয় না।** ZIP শুধু একটা
> ZIP হিসেবেই থাকবে—ভেতরের code repo-তে দেখা বা চালানো যাবে না।
> Repo আকারে রাখতে হলে ফাইলগুলো সত্যিকারের file হিসেবে push করতে হয়,
> আর মোবাইলে তার সবচেয়ে নির্ভরযোগ্য উপায় Termux + Git।

## পথ ক — নতুন আলাদা repo (সবচেয়ে পরিষ্কার)

### ১) ফোনে package টা বের করো
1. এই chat থেকে `1Fill2Blank-Tools.zip` download করো।
2. Files app বা ZArchiver দিয়ে Download folder-এ extract করো।
   শেষে এমন একটা folder থাকবে: `Download/1Fill2Blank-Tools/`

### ২) GitHub-এ সম্পূর্ণ খালি repo বানাও (মোবাইল browser)
1. Chrome-এ github.com-এ login করে **+ → New repository**।
2. নাম দাও যেমন `1Fill2Blank-Tools`।
3. **"Add a README", .gitignore বা licence কোনোটাই টিক দেবে না**
   — repo একদম খালি থাকতে হবে (এই package-এ নিজের README/.gitignore আছে)।
4. Create repository।

### ৩) Termux থেকে একটিমাত্র script চালাও
```bash
termux-setup-storage          # প্রথমবার হলে storage permission দাও
cd ~/storage/downloads/1Fill2Blank-Tools
bash mobile/termux_push.sh
```

Script নিজে যা করবে: Git আছে কিনা দেখবে → নাম/email না থাকলে চাইবে →
খালি repo-র **পরিষ্কার** HTTPS URL চাইবে (যেমন
`https://github.com/USER/1Fill2Blank-Tools.git`) → সব file সাজিয়ে
commit করবে → push-এর আগে সম্মতি চাইবে।

Push-এর সময় GitHub login চাইলে:
- **Username:** তোমার GitHub username
- **Password:** account password নয়। নিজের ফোনেই একটা
  **fine-grained token** বানিয়ে সেটা দাও:
  GitHub → Settings → Developer settings → Personal access tokens →
  Fine-grained tokens → শুধু এই একটি repo select করো →
  **Contents: Read and write** → মেয়াদ যত কম রাখা যায়।
- টাইপ করার সময় token পর্দায় দেখা যাবে না—এটাই স্বাভাবিক।
- কাজ শেষে চাইলে token টা GitHub থেকে delete করে দিতে পারো।

Script ইচ্ছা করে token যুক্ত URL (যেমন `https://TOKEN@github.com/...`)
দেখলেই থেমে যায়, যাতে ভুলেও token কোথাও জমা না হয়ে যায়।

## পথ খ — বিদ্যমান `1Fill2Blank` repo-র ভেতরে `tools/` folder

```bash
cd ~
git clone https://github.com/myabdur2121-cpu/1Fill2Blank.git
mkdir -p 1Fill2Blank/tools
cp -r ~/storage/downloads/1Fill2Blank-Tools 1Fill2Blank/tools/audio-video
cd 1Fill2Blank
rm -rf tools/audio-video/.git      # যদি থেকে থাকে
git status                         # কী যাচ্ছে নিজের চোখে দেখো
git add tools/audio-video
git commit -m "Add audio-video production tools"
git push
```

(এই repo-র বর্তমান `.gitignore` MP4 বাদ দেয়; এই package-এ MP4 নেই,
তাই music/script/docs সবই যাবে।)

## পথ গ — শুধু backup

Code আকারে না রেখে শুধু সংরক্ষণ চাইলে ZIP টাই যথেষ্ট: ফোনের
storage, Google Drive, অথবা যেকোনো GitHub repo-র একটি **Release**-এর
সঙ্গে asset হিসেবে attach করে রাখতে পারো। তখন লোকে ZIP download
করতে পারবে, কিন্তু repo-র file তালিকায় ভেতরের code দেখা যাবে না।

## নিরাপত্তা তালিকা (প্রতিবার)

- [ ] Token chat-এ পাঠাইনি তো?
- [ ] Token কোনো ফাইল, screenshot বা repo URL-এর ভেতরে নেই তো?
- [ ] Push-এর আগে `git status` দেখেছি তো? (`.gitignore` সিট বেল্ট মাত্র,
      চোখে দেখা যাচাইয়ের বিকল্প নয়)
- [ ] Token শুধু দরকারি একটি repo ও Contents Read/Write-এ সীমিত তো?
- [ ] আগে কখনো কোথাও পাঠানো token থাকলে সেটা GitHub থেকে
      delete/revoke করেছি তো?

## মোবাইল browser দিয়ে সরাসরি upload কেন সেরা পথ নয়

GitHub ওয়েবসাইটে **Add file → Upload files** দিয়ে কয়েকটা ফাইল তোলা
যায়, কিন্তু এই package-এর মতো অনেক folder-ওয়ালা কাঠামো মোবাইল
browser দিয়ে তোলা ঝামেলার ও ভুলপ্রবণ। এক-দুটো ফাইল বদলাতে ওটা ঠিক
আছে; পুরো package-এর জন্য Termux পথটাই নির্ভরযোগ্য।
