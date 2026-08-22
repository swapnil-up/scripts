#!/bin/bash
# nepali-cheatsheet.sh — searchable rofi reference for the Nepali
# transliteration engine (m17n:ne:rom-translit).
#   Toggle Nepali: Super+Shift+Space   |   This popup: $mod+Shift+s
# Selecting a row just dismisses the popup; Esc also closes it.

rofi -dmenu -i -p "Nepali cheatsheet — type to search (Esc to close)" <<'EOF'
——— vowels ———
a → अ
aa / A → आ
i → इ
ii / I / ee → ई
u → उ
uu / U / oo → ऊ
rri → ऋ
e → ए
ai → ऐ
o → ओ
au → औ
OM / AUM → ॐ
——— vowel signs (after consonant; ka = क) ———
aa / A → ा   (kaa → का)
i → ि        (ki → कि)
ii / I / ee → ी  (kii → की)
u → ु        (ku → कु)
uu / U / oo → ू  (kuu → कू)
rri → ृ      (krri → कृ)
e → े        (ke → के)
ai → ै       (kai → कै)
o → ो        (ko → को)
au → ौ       (kau → कौ)
——— consonants ———
k / q / c → क
kh → ख
g → ग
gh → घ
ng → ङ
ch → च
chh → छ
j / z → ज
jh → झ
yn → ञ
T → ट
Th → ठ
D → ड
Dh → ढ
n/ → ण
t → त
th → थ
d → द
dh → ध
n → न
p → प
f / ph → फ
b → ब
bh → भ
m → म
y → य
r → र
l → ल
v / w → व
sh → श
Sh / shh → ष
s → स
h → ह
ksh → क्ष
x / ks → क्स   (halant stays visible; for क्ष use ksh)
gyn → ज्ञ
——— conjuncts ———
ksh → क्ष   (not "ks")
shr → श्र   (shra)
gyn → ज्ञ
tra → त्र
pra → प्र
kra → क्र   (k\ra keeps halant visible instead)
sta → स्त
——— specials ———
M / N → ं  (anusvara; nM → नं)
H → ः      (visarga; dH → दः)
* → ँ      (chandrabindu; n* → नँ)
\ → ्      (halant; k\ → क्)
. → ।      (danda)
.. → ॥     (double danda)
~a → ऽ     (avagraha)
——— digits ———
0 → ०   1 → १   2 → २   3 → ३   4 → ४
5 → ५   6 → ६   7 → ७   8 → ८   9 → ९
——— tips ———
Consecutive consonants auto-halant: kk → क्क
Backspace undoes one transliteration step
EOF
