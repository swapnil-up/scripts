# Nepali transliteration cheatsheet (`m17n:ne:rom-translit`)

Type Latin phonetically; the engine converts as you type. E.g. `namaste` → नमस्ते.

**Toggle Nepali on/off:** `Super+Shift+Space` (global, works in any app)
**This cheatsheet:** `$mod+Shift+s` in i3 (searchable rofi popup)

A consonant followed directly by another consonant gets a halant automatically:
`kk` → क्क, `nma` → न्म. If it merges two sounds you don't want, press `Backspace` to
step back one transliteration unit.

## Common conjuncts (type the code on the left)

| Intended | Type | Result |
|---|---|---|
| क्ष | `ksh` | क्ष |
| श्र | `shr` | श्र |
| ज्ञ | `gyn` | ज्ञ |
| त्र | `tra` | त्र |
| प्र | `pra` | प्र |
| क्र | `kra` | क्र |
| स्त | `sta` | स्त |

Gotchas: `ks` → क्स (ka+virama+sa, halant stays visible) — for the क्ष glyph use
`ksh`, not `ks`. There is no `shra`/`shrya` key; `shr` covers श्र.

## Vowels (independent)

| Latin | Devanagari | Latin | Devanagari |
|---|---|---|---|
| `a` | अ | `o` | ओ |
| `aa` / `A` | आ | `au` | औ |
| `i` | इ | `rri` | ऋ |
| `ii` / `I` / `ee` | ई | `rree` | ॠ |
| `u` | उ | `OM` / `AUM` | ॐ |
| `uu` / `U` / `oo` | ऊ | | |
| `e` | ए | | |
| `ai` | ऐ | | |

## Vowel signs (after a consonant)

A bare `a` after a consonant gives the inherent vowel (no sign): `ka` → क.
Use these for the other vowels: `ki` → कि, `ku` → कु.

| Latin | Sign | Example |
|---|---|---|
| `aa` / `A` | ा | `kaa` → का |
| `i` | ि | `ki` → कि |
| `ii` / `I` / `ee` | ी | `kii` → की |
| `u` | ु | `ku` → कु |
| `uu` / `U` / `oo` | ू | `kuu` → कू |
| `rri` | ृ | `krri` → कृ |
| `e` | े | `ke` → के |
| `ai` | ै | `kai` → कै |
| `o` | ो | `ko` → को |
| `au` | ौ | `kau` → कौ |

## Consonants

| Latin | Devanagari | Latin | Devanagari |
|---|---|---|---|
| `k` / `q` / `c` | क | `T` | ट |
| `kh` | ख | `Th` | ठ |
| `g` | ग | `D` | ड |
| `gh` | घ | `Dh` | ढ |
| `ng` | ङ | `n/` | ण |
| `ch` | च | `t` | त |
| `chh` | छ | `th` | थ |
| `j` / `z` | ज | `d` | द |
| `jh` | झ | `dh` | ध |
| `yn` | ञ | `n` | न |
| `p` | प | `y` | य |
| `f` / `ph` | फ | `r` | र |
| `b` | ब | `l` | ल |
| `bh` | भ | `v` / `w` | व |
| `m` | म | `s` | स |
| `sh` | श | `h` | ह |
| `Sh` / `shh` | ष | `ksh` | क्ष |
| `x` / `ks` | क्स | `gyn` | ज्ञ |

## Special characters

| Latin | Devanagari | Meaning |
|---|---|---|
| `M` / `N` | ं | anusvara (`nM` → नं) |
| `H` | ः | visarga (`dH` → दः) |
| `*` | ँ | chandrabindu (`n*` → नँ) |
| `\` | ् | halant — kill the vowel (`k\` → क्) |
| `.` | । | danda (full stop) |
| `..` | ॥ | double danda |
| `~a` | ऽ | avagraha |

## Digits

| Latin | `0` | `1` | `2` | `3` | `4` | `5` | `6` | `7` | `8` | `9` |
|---|---|---|---|---|---|---|---|---|---|---|
| Nepali | ० | १ | २ | ३ | ४ | ५ | ६ | ७ | ८ | ९ |
