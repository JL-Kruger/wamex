# WAMEX - The wa.me Extractor — 

This was the project that made me understand why AI is a pretty big deal. My idiot ass would have tackled the precise problem this app solves in the dumbest way possible: manual brute force. I had to migrate a group to a community without losing 400+ pending requests. I was gonna get those numbers manually because spam and bot filters and just the whole bitch-ass catastrophuck that is WhatsApp. Instead, because I knew that at least part of the process could be automated (even if I didn't know how) then it might be worth figuring some of this out.

It's not fancy, by any stretch of the imagination, but it doesn't need to be. you give it a mangled mess of text with phone numbers in there somewhere, it finds the numbers and structures them as wa.me links. If the phone number ain't on whatsapp, or they have specifically blocked the feature, then you're shit out of luck sweetheart. This isn't for that. 

Anyway, it has a very very niche set of uses, but for community managers on whatsapp, or anybody looking to make a list of direct message links, this is a tool that might be of use. I make no guarantees about the safety of this software. I probably will never update it, unless I need it for something other than its current purpose.

It would be better to leave WhatsApp entirely in my opinion, but I will usually keep at least some semblance of a connection to the places where most people are.

Soon, my pretties... Soon we will be free of the scourge of Meta and the other Madmen that hath wrought this nonsense upon us.

Thanks for reading my not-TED-talk.

okay bye.

PS: this tool saved me weeks, and I built it with a bot in under half an hour with only the vaguest understanding of what I needed to acheive, and a reasonable grasp of context management and agentic workflows. I would never have even considered this a viable solution 18 months ago. Shit is wild, people.

## Setup

## Requirements

Python 3.10+ (uses `match` syntax / union types in hints)

### Install dependencies

```bash
pip install beautifulsoup4
```

`tkinter` ships with most Python installations on Linux.
If it's missing:
```bash
# Debian/Ubuntu
sudo apt install python3-tk

# Arch
sudo pacman -S tk

# Fedora
sudo dnf install python3-tkinter
```

---

## Run

```bash
python wa_extractor.py
```

---

## Workflow

1. In WhatsApp Web, open the pending requests panel.
2. Right-click the outer div containing all requests → **Inspect**.
3. In DevTools, right-click the `<div>` element → **Copy** → **Outer HTML**.
4. Paste into a `.txt` file (or directly into the left pane of the app).
5. Hit **⚡ extract**.
6. Adjust batch size if needed (default 20 — good for spam-safe manual invites).
7. **Save .txt** or **Copy all** to share with your community admins.

---

## Output format

```
https://wa.me/+27821234567
https://wa.me/+27831234567
...  (20 links)

────────────────────────────────────────
https://wa.me/+27841234567
...
```

Each block = one admin's batch for the day.
