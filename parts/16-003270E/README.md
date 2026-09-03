# CONEC 16-003270E — SnapLock-Clip, Raststift, Federscheibe

Teile aus dem Amphenol/CONEC-Haubensatz **16-003270E** (Kunststoffhaube
25-pol. mit SnapLock-Schnellverriegelung, Zeichnung 16K1A4424, Datenblatt in
diesem Ordner), die für den **SD-AC1-DS** gebraucht werden: die zwei
**Federclips** (Edelstahl 0,5 mm) kommen in das gedruckte Adaptergehäuse,
die zwei **Raststifte** (4-40 UNC, vernickelt) mit **Federscheiben** werden
in den Steckverbinder der Gegenseite geschraubt. Beim Aufstecken schnappt
die Gabel im Fuß des Clips über die Kuppe des Stifts und sitzt dann in
seinem Hals; gelöst wird durch Ziehen.

CONEC liefert für den Clip keine CAD-Daten. Das Modell ist aus der
Haubenzeichnung abgegriffen (Maßstab 1,5:1 auf A3, als A4 gedruckt =
25,0 px/mm bei 600 dpi, geeicht an 55,4 / 41,5 / 15,4 mm), Genauigkeit
etwa ±0,1 mm. Der Abgleich Modell gegen Zeichnung liegt als
`*_zeichnungsabgleich.png` bei.

| Datei | Inhalt |
| --- | --- |
| `CONEC_16-003270E_SnapLock_Clip.step` | Clip, für Onshape-Import |
| `CONEC_16-003270E_Raststift_4-40.step` | Raststift mit echtem 4-40-Gewinde |
| `CONEC_16-003270E_Federscheibe.step` | Sprengring Nr. 4 |
| `*_dreiseitenansicht.png` | Kontrollblätter mit Sollmaßen (Clip, Stift) |
| `CONEC_16-003270E_SnapLock_Clip_zeichnungsabgleich.png` | Modellschnitte des Clips über der CONEC-Zeichnung |
| `CONEC_16-003270E_Raststift_4-40_render.png` | Produktbild Stift + Federscheibe |
| `create_snaplock_clip_step.py` | Clip-Generator (CadQuery), alle Maße als Konstanten |
| `create_detent_pin_step.py` | Generator Stift + Federscheibe (`simple` = Onshape-tauglich, `helix` = echtes Gewinde) |
| `check_against_drawing.py` | erzeugt den Zeichnungsabgleich des Clips |
| `render_checks.py`, `render_checks_pin.py` | erzeugen die Kontrollblätter (Blender headless) |
| `onshape_assemble.py` | Upload nach Onshape und Platzierung in der SD-AC1-DS-Assembly |

```
.venv/bin/python parts/16-003270E/create_snaplock_clip_step.py
.venv/bin/python parts/16-003270E/create_detent_pin_step.py
.venv/bin/python parts/16-003270E/check_against_drawing.py
.venv/bin/python parts/16-003270E/render_checks.py
.venv/bin/python parts/16-003270E/render_checks_pin.py
```

## Bezugssystem Clip

Ursprung auf der **Achse des Raststifts**, z = 0 an der Unterseite des
Fußes (tiefster Punkt), +z = Steckrichtung (der Stift zeigt nach +z),
+x nach außen durch die Gehäusewand, y quer; der Clip ist zu y = 0
symmetrisch. Derselbe Körper passt auf beide Seiten (um z um 180° gedreht).

Im verriegelten Zustand liegt der Gabelfuß (z = 0 … 0,5) im Hals des
Raststifts. Der Stift ist in seinem eigenen System modelliert (siehe
unten); zum Zusammenbau seine Achse auf die z-Achse des Clips legen und
den Hals (Stift-z −6,6 … −7,0) auf Clip-z 0 … 0,5 setzen, d. h.
Stift-z = −(Clip-z + 6,6) … der Sechskant sitzt dann bei Clip-z −1,8 …
−6,6, die Kuppe reicht bis Clip-z 2,7.

Stiftabstand = Lochabstand des Steckverbinders: HD-26 (Schalengröße A wie
DA15) 33,32 mm, DB25 47,04 mm. In der CONEC-Haube liegt die
54,4-mm-Seitenwand bei x = 3,7; der Außenschenkel steht etwa 1,1 mm
darüber hinaus, das Oberteil sitzt in einem Wandschlitz bei x = 2,1 … 3,0.

## Aufbau Clip

- **Gabelfuß** waagerecht, läuft bis x = −1,3 über die Stiftachse hinaus,
  mit 2,5 mm breitem Schlitz (nach innen offen, halbrund geschlossen bei
  x = 3,4). Die beiden Arme sind die Rastfedern; Bogen 90°, Innenradius 0,2.
  `FOOT_VARIANT = 'short'` baut die frühere Lesart (Fuß nur bis x = 2,85,
  ohne Schlitz).
- **Außenschenkel** um 1,8° geneigt (unten weiter außen); unten als
  **Lappen 5,1 breit**, ab z = 1,75 volle Breite 11,6 mit R 0,9 an den
  Ecken und R 0,3 in der Hohlkehle.
- **Fenster** 5,6 breit, z = 2,95 … 13,0, Ecken R 1,45.
- **Zunge** 3,5 breit, hängt vom Steg herab, ab z = 9,4 um 4,8° nach innen
  geneigt, Spitze z = 3,65, Spitzenecken R 0,3. Sie berührt den Stift nicht
  (in der Haube liegt zwischen Zungenschlitz und Stiftbohrung eine
  geschlossene Wand), sondern spannt den Clip im Wandschlitz vor.
- **Kröpfung** 45°, 1,56 nach innen, z = 10,3 … 11,8; **Oberteil** senkrecht
  bei x = 2,47 … 2,97, Oberkante z = 14,6.

## Raststift und Federscheibe

Bezugssystem wie bei den Schraubteilen in `screws/`: z = 0 an der
Anlagefläche des Sechskants, +z zur Gewindespitze, Kopf bei negativem z.
Die Federscheibe liegt im selben System bei z = 0 … 1,2 (entspannt).

- **Gewinde** 4-40 UNC-2A, 4,5 lang, Anschnitt C 0,3. Die ausgelieferte
  STEP-Datei trägt das Gewinde als glatten Zylinder auf dem Nenndurchmesser
  (`THREAD_STYLE = 'simple'`): das echt geschnittene Helix-Gewinde
  (`helix`, Datei `*_gewinde.step`) besteht zwar OCCs Gültigkeitsprüfung,
  hinterlässt an der Gewindestirn aber eine Splitterfläche von 1e-5 mm²,
  und Onshape importiert es dann nur als Oberfläche (02.09.2026). Für
  Assembly und Zeichnung reicht der Zylinder.
- **Sechskant** SW 4,8 × 4,8, abgedrehte Fasen C 0,2 unten / C 0,4 oben.
- **Bund** Ø 3,1 × 1,8 · **Hals** Ø 2,6 × 0,6 (Gabel 0,5 + Spiel) ·
  **Kuppe** Ø 3,0, 2,3 hoch, oben Fläche Ø 1,0 mit Körnermarke. Kopf über
  dem Sechskant 4,7, Stift gesamt 14,0.
- **Federscheibe** Sprengring Nr. 4 (ASME B18.21.1): Ø 2,95 / 5,3 × 0,64,
  flach modelliert (wie unter dem Sechskant verbaut; `WASHER_RISE` > 0
  ergibt die aufgebogene Form).

Quellen: Sechskant und Gewinde sind Normmaße der D-Sub-Befestigung (wie
BKL 10120256). Bund, Hals und Kuppe sind aus der 3D-Ansicht des Datenblatts
(Verhältnis zum Gewinde-Ø 2,845 und zur Sechskanthöhe) abgegriffen und am
Prototypfoto `sdlink-manuals/assets/images/sd-ac1-ds/sd-ac1-ds_2.png`
gegengeprüft: ±0,2 mm, Gewindelänge ±0,5 mm. Die Haubenzeichnung bemaßt
den Stift nicht; die Kugelkontur Ø 4,3 in ihrem Schnitt ist die
Stiftkammer der Haube, nicht der Stift.

## Onshape (SD-AC1-DS, Dokument 9d9be5d218fd741d3272e193)

Stand 02.09.2026: alle drei Teile sind als benannte Part Studios im
Dokument (`SnapLock-Clip 16-003270E` 2e89e533…, `Raststift 4-40 UNC
16-003270E` 8441d752…, `Federscheibe 16-003270E` c671cac5…) und in der
Assembly „Zusammenbau" je zweimal eingefügt und platziert; mit dem Gehäuse
sind sie in „Gruppe CONEC-Satz" zusammengefasst. Die älteren Studios
`CONEC_16-003270E_SnapLock_Clip` (Klammer, alter Fuß) und
`CONEC_16-003270E_Federscheibe` samt Blobs sind nicht mehr referenziert und
können gelöscht werden.

Die Bauteilnamen kommen aus dem STEP (Export über eine einteilige
CadQuery-Assembly, `export_named`), sonst heißt alles „Part 1".

Platzierung (`onshape_assemble.py place`), abgeleitet aus den
Transformationen der NorComp-Steckverbinder in der Assembly:

- **Clips** an den Befestigungslöchern der Buchse 180-026-213R001, Clip-z = 0
  bei 1,45 mm hinter der Flansch-Vorderseite, +z in das Gehäuse. Herleitung:
  Raststift des AC-1 auf dessen Flansch (= Spitze der Buchsenschale, 5,84):
  Scheibe 0,64 + Sechskant 4,8 + Bund 1,8 → Hals bei −1,40 … −2,00, die
  Gabel sitzt mittig darin. Der Bund Ø 3,1 läuft durch das Flanschloch
  Ø 3,05 der Buchse.
- **Raststifte + Federscheiben** auf der Flansch-Vorderseite des Steckers
  180-026-113R001, Scheibe 0,64 unter dem Sechskant, Gewinde in den Flansch.

Zugang: `~/.config/onshape/credentials_write.json` (Key mit Write-Scope);
die Lese-Skripte in `prodflux/scripts/` nutzen weiter `credentials.json`.

### Schriftzug „fürs Foto"

Der SD-Link-Schriftzug liegt beim Drucken 0,15 mm unter der Oberfläche
(Skizze 15/„Linear austragen 19" auf der Body-Unterseite, Skizze 16/„Linear
austragen 20" auf der Cover-Oberseite: Entfernen mit Startversatz 0,15 und
Tiefe 0,15) und schimmert nur durch. Für Zeichnung und Renderings gibt es
wie in den anderen Adapter-Dokumenten je ein Extrude **„fürs Foto"**, das
dieselben Skizzenregionen ohne Versatz 0,1 mm von der Oberfläche her
ausschneidet (Features `FSCI7HyNHC4UqeY_4`, `FG1pPc3dV8aADlr_4`).

```
onshape_assemble.py foto on      # Schnitte aktiv → Modell fürs Foto
onshape_assemble.py foto off     # unterdrücken → Druckmodell
onshape_assemble.py drawing out.pdf   # Zeichnung „Assembly 1 Drawing 1" als PDF
```

Vor dem Drucken müssen die Schnitte unterdrückt sein (`foto off`).
`SD-AC1-DS_assembly_fuersFoto.glb` ist die Assembly mit sichtbarem
Schriftzug für Renderings (`render_assembly.py`), das Produktbild
`SD-AC1-DS_assembly_render.png` ist daraus entstanden.

Grenze der API: Die Zeichnung berechnet ihre Ansichten erst beim Öffnen im
Browser neu. Ein PDF-Export per API liefert den zuletzt berechneten Stand,
auch nach Modify-Aufrufen; also Zeichnung einmal öffnen, dann exportieren.

## Annahmen und was am echten Teil zu prüfen ist

- **Gabelfuß:** Länge über die Stiftachse hinaus (1,3) stammt aus dem
  Haubenschnitt; Schlitzbreite (2,5) und geschlossenes Ende (x = 3,4) sind
  angenommen. Am echten Clip prüfen: hat der Fuß einen Schlitz, wie breit,
  wie lang ist der Fuß ab Außenfläche (Modell 6,15)?
- Das obere Fensterende ist in der Zeichnung von der Wand verdeckt;
  angenommen z = 13,0 (Steg 1,6 hoch).
- Die Zungenspitze ist glatt modelliert; die Zeichnung deutet eine kleine
  Nase nach innen an.
- Weitere Kontrollmaße am Clip: Lappenbreite 5,1, Gesamthöhe 14,6, Breite 11,6.
- Am Stift: Bundhöhe (1,8) und Halsdurchmesser (2,6) mit dem Messschieber
  prüfen, die Gabel des Clips muss dazu passen.
