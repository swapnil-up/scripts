# Conky Desktop Dashboard

This directory contains a modular Conky-based desktop dashboard designed for
**ambient awareness**, not constant interaction.

Each widget is its own Conky instance. Together, they form a persistent
background layer that surfaces important context while staying visually quiet.

No Chromium, no Electron, no database.
Just shell scripts, text files, and Conky.

---

## Overview

The dashboard is composed of **six widgets**, positioned around a 1366×768 screen:

1. Todo
2. Stats
3. Recent Notes
4. Quotes
5. Year Progress
6. Sunrise/Sunset
7. XKCD

Each widget:
- Runs independently
- Uses transparent windows
- Sits below normal application windows
- Can be enabled/disabled without affecting the others

---

## Screenshot

![Conky dashboard overview](screenshots/overview.png)

---

## Widgets

### 1. Todo (`conky_todo.conf`)

Displays the current todo list.

- Source: `todo.txt`
- Plain text, human-editable
- Rendered as a simple list

Purpose:
Immediate tasks without task-manager overhead.
Links great with rofi which does the editing

---

### 2. Stats (`conky_stats.conf`)

Shows lightweight activity metrics.

- GitHub:
  - Commits today (`github_today.sh`)
  - Commits this week (`github_week.sh`)
- Anki:
  - Reviews today (`anki_today.sh`)
  - Reviews this week (`anki_week.sh`)

Purpose:
How's the progress going?

---

### 3. Recent Notes (`conky_notes.conf`)

Lists recently modified Obsidian notes.

- Source: `obsidian_last_notes.sh`
- Derived from the filesystem, not Obsidian internals

Purpose:
Surface recent thinking without opening the obsidian vault. Acts as a gentle nudge to get back into writing.

---

### 4. Quotes (`conky_quotes.conf`)

Displays a single quote that changes periodically.

- Source: `quotes.txt`
- One quote per line
- Randomly selected
- Fixed max width with automatic text wrapping

Purpose:
Mix of philosophy, humor, and programming wisdom. A cookie treat for the soul.

---

### 5. Year Progress (`conky_year.conf`)

Visualizes the passage of the year as dots, grouped by month.

- Script: `scripts/year_dots.sh`
- 12 rows → one per month
- Each dot represents a day:
  - ● past
  - ◉ today
  - ○ future
- No numbers, no percentages

Purpose:
Time awareness without abstraction. So fucking cool. Thanks Sagar.

---

### 6. Sunrise/Sunset (`conky_sunrise.conf`)

Shows today's sunrise, sunset, and day length for Kathmandu.

- Script: `scripts/sunrise_sunset.sh`
- API: sunrise-sunset.org
- Converts UTC to local time (UTC+5:45)

Purpose:
Know the shape of your day. When does light start, when does it end.

---

### 7. XKCD (`conky_xkcd.conf`)

Displays a random XKCD comic with title and alt text.

- Script: `scripts/xkcd_random.sh`
- Fetches random comic via XKCD JSON API
- Downloads image to `/tmp/conky_xkcd/`
- Shows comic image + title + alt text

Purpose:
A moment of geek humor. Because sometimes you need to laugh at a penguin comic.

---

## Directory Structure

./
├── screenshots/
├── scripts/
│   ├── anki_today.sh*
│   ├── anki_week.sh*
│   ├── github_today.sh*
│   ├── github_week.sh*
│   ├── obsidian_last_notes.sh*
│   ├── sunrise_sunset.sh*
│   ├── year_dots.sh*
│   └── xkcd_random.sh*
├── conky_notes.conf
├── conky_quotes.conf
├── conky_stats.conf
├── conky_sunrise.conf
├── conky_todo.conf
├── conky_xkcd.conf
├── conky_year.conf
├── quotes.txt
├── README.md
├── secrets.env
└── todo.txt

2 directories, 17 files

---

## Notes

- Widgets are started individually from the i3 config
- Reloading i3 does not reload Conky
- Each widget can be restarted independently
- Scripts are intentionally simple and inspectable

---