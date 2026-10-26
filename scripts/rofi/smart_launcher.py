#!/usr/bin/env python3

import shutil
import sys
import os
import json
import subprocess
import time
from pathlib import Path
from configparser import ConfigParser
from datetime import datetime
from urllib.parse import quote_plus

CACHE_DIR = Path.home() / ".cache/rofi-launcher"
APPS_CACHE = CACHE_DIR / "apps.json"
USAGE_CACHE = CACHE_DIR / "usage.json"

DESKTOP_DIRS = [
    Path("/usr/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/snapd/desktop/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
    Path.home() / ".local/share/flatpak/exports/share/applications",
]

CACHE_TTL = 3600  # seconds
APPS_CACHE_VERSION = 2

COMMANDS = [
    ("Run shell command", "./"),
    ("Toggle todo", ",tt"),
    ("Add todo", ",t"),
    ("Remove todo", ",tr"),
    ("Archive completed todos", ",ta"),
    ("Set / cancel timer", ",timer"),
    ("Shut down / cancel / extend", ",off"),
    ("New note", ",n"),
    ("New TIL", ",til"),
    ("New why note", ",why"),
    ("Append to hmm", ",hmm"),
    ("Log annoyance", ",mf"),
    ("Web search (gh/yt/lb/wiki)", ",w"),
    ("Text to speech", ",piper"),
    ("Speech to text", ",whisper"),
    ("Audio transcribe", ",at"),
]

ALIASES = [
    {
        "key": "tend",
        "label": "Tend notes",
        "mode": "picker",
        "cmd": "~/github/scripts/scripts/rofi/rofi-tend-menu.sh",
    },
    {
        "key": "bootstrap",
        "label": "Run full bootstrap",
        "mode": "terminal",
        "cmd": "~/github/scripts/setup/bootstrap.sh",
    },
    {
        "key": "crawler",
        "label": "Web crawler",
        "mode": "terminal",
        "cmd": "python3 ~/github/scripts/scripts/python/crawler.py",
    },
    {
        "key": "k",
        "label": "Restart kanata",
        "mode": "quiet",
        "cmd": "systemctl --user restart kanata",
    },
    {
        "key": "newip",
        "label": "New WARP IP",
        "mode": "quiet",
        "cmd": "~/github/scripts/scripts/warp-new-ip.sh",
    },
    {
        "key": "docker-clean",
        "label": "Prune docker",
        "mode": "terminal",
        "cmd": "docker container prune -f; docker image prune -f; docker network prune -f; docker volume prune -f",
    },
    {
        "key": "clickpaste",
        "label": "Type clipboard",
        "mode": "detached",
        "cmd": "notify-send 'Clickpaste' 'Typing clipboard in 3 seconds'; sleep 3; xdotool type \"$(xclip -o -selection clipboard)\"",
    },
]


def entry_display(label, alias):
    return f"{label:<34} {alias}"


def alias_display(alias):
    return entry_display(alias["label"], f",{alias['key']}")


def index_apps():
    apps = []
    seen = set()

    for base in DESKTOP_DIRS:
        if not base.exists():
            continue

        for path in sorted(base.glob("*.desktop")):
            cp = ConfigParser(interpolation=None)
            try:
                cp.read(path)
                entry = cp["Desktop Entry"]
            except Exception:
                continue

            if entry.get("Type") != "Application":
                continue
            if entry.get("NoDisplay", "false").lower() == "true":
                continue
            if entry.get("Hidden", "false").lower() == "true":
                continue

            name = entry.get("Name")
            exec_cmd = entry.get("Exec")

            if not name or not exec_cmd:
                continue
            if exec_cmd.strip() == "/usr/bin/false" or name in seen:
                continue

            seen.add(name)
            apps.append(
                {
                    "name": name,
                    "desktop_id": path.stem,
                }
            )

    return sorted(apps, key=lambda app: app["name"].casefold())


def load_apps():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if APPS_CACHE.exists():
        age = time.time() - APPS_CACHE.stat().st_mtime
        if age < CACHE_TTL:
            try:
                cached = json.loads(APPS_CACHE.read_text())
            except (OSError, ValueError):
                cached = None
            if (
                isinstance(cached, dict)
                and cached.get("version") == APPS_CACHE_VERSION
                and isinstance(cached.get("apps"), list)
            ):
                return cached["apps"]

    apps = index_apps()
    APPS_CACHE.write_text(json.dumps({"version": APPS_CACHE_VERSION, "apps": apps}))
    return apps


def load_usage():
    try:
        data = json.loads(USAGE_CACHE.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(key): float(value)
        for key, value in data.items()
        if isinstance(value, (int, float))
    }


def record_usage(key):
    usage = load_usage()
    usage[key] = time.time()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        USAGE_CACHE.write_text(json.dumps(usage))
    except OSError:
        pass


def cmd_key(alias):
    return alias[1:] if alias.startswith(",") else alias


def mru_sort(items, key_fn, usage):
    """Order kept for never-used items; most recently used float to the top."""
    return [
        item
        for _, item in sorted(
            enumerate(items),
            key=lambda pair: (-usage.get(key_fn(pair[1]), 0.0), pair[0]),
        )
    ]


def build_candidates():
    usage = load_usage()
    items = ["Terminal"]

    items += [
        entry_display(label, alias)
        for label, alias in mru_sort(
            COMMANDS, lambda command: f"cmd:{cmd_key(command[1])}", usage
        )
    ]
    items.append("---")
    items += [
        alias_display(alias)
        for alias in mru_sort(ALIASES, lambda a: f"alias:{a['key']}", usage)
    ]
    items.append("---")

    # apps
    apps = sorted(
        load_apps(),
        key=lambda app: (
            -usage.get(f"app:{app['name']}", 0.0),
            app["name"].casefold(),
        ),
    )
    for app in apps:
        items.append(app["name"])

    return items


def output_menu():
    items = build_candidates()
    for item in items:
        print(item)


def launch_terminal(title, command, hold=True):
    term = os.environ.get("TERMINAL")
    if not term:
        term = "alacritty" if shutil.which("alacritty") else "x-terminal-emulator"
    suffix = "; echo; read -rp 'Press Enter to close.'" if hold else ""
    subprocess.Popen(
        [
            term,
            "--title",
            title,
            "-e",
            "bash",
            "-lc",
            f"{os.path.expanduser(command)}{suffix}",
        ]
    )


def run_alias(alias):
    record_usage(f"alias:{alias['key']}")
    cmd = os.path.expanduser(alias["cmd"])
    mode = alias["mode"]

    if mode == "picker":
        subprocess.Popen(["bash", "-lc", cmd])
    elif mode == "terminal":
        launch_terminal(f"Alias — {alias['label']}", cmd)
    elif mode == "quiet":
        result = subprocess.run(cmd, shell=True, executable="/bin/bash")
        if result.returncode:
            subprocess.run(
                ["notify-send", "-u", "critical", alias["label"], "Command failed"]
            )
        else:
            subprocess.run(["notify-send", alias["label"]])
    else:
        subprocess.Popen(cmd, shell=True, executable="/bin/bash")


def dispatch(raw):
    if not raw:
        return

    raw = raw.strip()

    for alias in ALIASES:
        if raw == alias_display(alias):
            run_alias(alias)
            return

    command = dict(
        (entry_display(label, alias), alias) for label, alias in COMMANDS
    ).get(raw)
    if command:
        raw = command

    # Strip descriptions from older command rows.
    if raw.startswith(",") and " — " in raw:
        raw = raw.split(" — ", 1)[0].strip()

    # 1. SHELL MODE
    if raw == "./":
        typed = subprocess.run(
            ["rofi", "-dmenu", "-p", "Shell command…", "-lines", "0"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not typed:
            return
        handle_bash(typed)
        return
    if raw.startswith("./"):
        cmd = raw[2:].strip()  # Strip the './'
        handle_bash(cmd)
        return

    # COMMAND MODE
    if raw.startswith(","):
        query = raw[1:]

        # split first space
        if " " in query:
            cmd, rest = query.split(" ", 1)
        else:
            cmd, rest = query, ""

        # split comma subcommands
        parts = cmd.split(",")
        base = parts[0]
        sub = parts[1] if len(parts) > 1 else None

        handle_command(base, sub, rest)
        return

    # APP MODE
    if not raw.startswith(","):
        apps_cache = load_apps()
        APP_MAP = {a["name"]: a["desktop_id"] for a in apps_cache}
        desktop_id = APP_MAP.get(raw)
        if desktop_id:
            record_usage(f"app:{raw}")
            subprocess.run(["gtk-launch", desktop_id])
        else:
            # fallback: try to exec as command
            if shutil.which(raw):
                record_usage(f"app:{raw}")
                subprocess.Popen([raw])
            else:
                subprocess.run(["notify-send", "Cannot launch app", raw])
        return


def handle_command(base, sub, rest):
    home = Path.home()

    if base in [
        "t",
        "tt",
        "tr",
        "ta",
        "n",
        "til",
        "why",
        "hmm",
        "timer",
        "off",
        "mf",
        "w",
        "piper",
        "whisper",
        "at",
    ]:
        record_usage(f"cmd:{base}")

    if base in ["t", "tt", "tr", "ta"]:
        if rest:
            subprocess.run(
                [home / "github/scripts/scripts/rofi/rofi-todo-add.sh", base, rest]
            )
        else:
            subprocess.run(
                [home / "github/scripts/scripts/rofi/rofi-todo-add.sh", base]
            )

    elif base in ["n", "til", "why", "hmm"]:
        if rest:
            subprocess.run(
                [home / "github/scripts/scripts/rofi/rofi-obsidian.sh", base, rest]
            )
        else:
            subprocess.run(
                [home / "github/scripts/scripts/rofi/rofi-obsidian.sh", base]
            )

    elif base == "timer":
        subprocess.run([home / "github/scripts/scripts/rofi/rofi-timer-menu.sh"])

    elif base == "off":
        args = [home / "github/scripts/scripts/rofi/rofi-shutdown-menu.sh"]
        if rest:
            args.extend(rest.split())
        subprocess.run(args)

    elif base == "mf":
        log_annoying()

    elif base == "w":
        if not rest:
            rest = subprocess.run(
                ["rofi", "-dmenu", "-p", "Search web…", "-lines", "0"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            if not rest:
                return
        if sub is None and " " in rest:
            first, remainder = rest.split(" ", 1)
            if first in {"gh", "yt", "lb", "wiki"}:
                sub, rest = first, remainder
        q = quote_plus(rest)
        if sub == "gh":
            url = f"https://github.com/search?q={q}"
        elif sub == "yt":
            url = f"https://youtube.com/results?search_query={q}"
        elif sub == "lb":
            url = f"https://libgen.li/index.php?req={q}"
        elif sub == "wiki":
            url = f"https://en.wikipedia.org/w/index.php?search={q}"
        else:
            url = f"https://google.com/search?q={q}"

        browser = shutil.which("firefox-dev") or shutil.which("firefox")
        if browser:
            subprocess.run([browser, url])
        else:
            subprocess.run(["xdg-open", url])

    elif base == "piper":
        launch_terminal("Piper TTS", "~/github/scripts/scripts/utils/piper.sh")

    elif base == "whisper":
        launch_terminal("Whisper STT", "~/github/scripts/scripts/utils/whisper.sh")

    elif base == "at":
        launch_terminal(
            "Audio transcribe", "~/github/scripts/scripts/audio-transcribe.sh"
        )

    else:
        subprocess.run(["notify-send", "Unknown command", f",{base}"])


def log_annoying():
    file = Path.home() / "notes/annoying.log"
    file.parent.mkdir(parents=True, exist_ok=True)

    entry = subprocess.run(
        ["rofi", "-dmenu", "-p", "annoying…", "-lines", "0"],
        capture_output=True,
        text=True,
    ).stdout.strip()

    if not entry:
        return

    with open(file, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} – {entry}\n")

    subprocess.run(["notify-send", "Logged annoyance", entry])


def handle_bash(cmd):
    """Executes a string as a bash command and notifies the user of the result."""
    try:
        process = subprocess.run(
            cmd, shell=True, executable="/bin/bash", capture_output=True, text=True
        )

        if process.returncode == 0:
            output = process.stdout.strip() or "Command executed successfully."
            subprocess.run(["notify-send", "Bash Success", output[:100]])
        else:
            error = process.stderr.strip() or "Unknown error"
            subprocess.run(["notify-send", "-u", "critical", "Bash Error", error[:100]])

    except Exception as e:
        subprocess.run(["notify-send", "Execution Failed", str(e)])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--dispatch":
        dispatch(sys.stdin.read().strip())
    else:
        output_menu()


if __name__ == "__main__":
    main()
