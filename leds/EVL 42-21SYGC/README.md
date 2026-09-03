# Everlight 42-21SYGC/S530-E2/TR8 — 1,8-mm-Rund-SMD-LED

Funktions-LED (gelbgrün, wasserklar) des **SD-AC1-DS**; sie sitzt mit der
Linse im Ø-2,5-Loch des Covers. Maße aus dem Datenblatt in diesem Ordner
(Package Outline Dimensions, Toleranz ±0,1 mm).

| Datei | Inhalt |
| --- | --- |
| `Everlight_42-21SYGC.step` | die LED, Bauteilname „LED 42-21SYGC Everlight" |
| `Everlight_42-21SYGC_dreiseitenansicht.png` | Kontrollblatt mit Sollmaßen |
| `create_led_step.py` | Generator (CadQuery) |
| `render_checks_led.py` | erzeugt das Kontrollblatt (Blender headless) |

Aufbau: Grundplatte 3,2 × 2,4 × 0,5 mit Lötfahnen an den Stirnseiten (innen
2,0 frei), Gehäusekörper 2,2 × 2,4 × 0,5, Linse Ø 1,8 als Zylinder 0,6 mit
Kuppe R 0,9, Gesamthöhe 2,5. Kathodenmarke als Eckfase des Körpers.
Bezugssystem: Ursprung in der Linsenachse auf der Lötebene, +z zur
Linsenspitze, x längs.

## Onshape

Als Part Studio „LED 42-21SYGC Everlight" (96592a78…) im Dokument SD-AC1-DS
und in „Zusammenbau" eingefügt. Verknüpft mit einem **Fastened-Mate** „Fastened
LED" zwischen der unteren Kreiskante der Cover-Bohrung (z = 15,3 im
Cover-System) und der Nahtkante der Linse (z = 1,6 der LED), Primärachse
gespiegelt: die LED-Achse liegt in der Bohrung, die Kuppe endet 0,1 mm unter
der Deckfläche, die Lötebene 1,6 mm unter der Cover-Innenseite. Angelegt mit
`parts/16-003270E/onshape_assemble.py mate-led flip` (dort steht auch, warum
nur der unversionierte Feature-Endpunkt implizite Mate-Connectoren annimmt).

Die Lötebene entspricht der Lage der Platine unter dem Cover; sobald die
Platine in der Assembly ist, das Mate bei Bedarf auf sie umhängen.
