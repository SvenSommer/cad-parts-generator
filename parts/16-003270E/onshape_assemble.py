"""Teile des CONEC-Satzes nach Onshape bringen und in der SD-AC1-DS-Assembly platzieren.

  .venv/bin/python parts/16-003270E/onshape_assemble.py upload <step> <Elementname>
  .venv/bin/python parts/16-003270E/onshape_assemble.py elements
  .venv/bin/python parts/16-003270E/onshape_assemble.py assembly
  .venv/bin/python parts/16-003270E/onshape_assemble.py place ...   (siehe unten)

Zugang: ~/.config/onshape/credentials_write.json (Key mit Write-Scope).
Dokument SD-AC1-DS: did 9d9be5d218fd741d3272e193, Workspace
12567d5c035363576ea21464, Assembly 1 ae4466fa5f1cff66c7bbab6d.

Upload = Blob-Element mit translate=true: Onshape übersetzt die STEP-Datei
in ein Part Studio (Name = Elementname); die Übersetzung läuft asynchron
und wird hier abgewartet.
"""
import json
import sys
import time
from pathlib import Path

import requests

B = 'https://cad.onshape.com/api/v6'
DID, WID, AID = '9d9be5d218fd741d3272e193', '12567d5c035363576ea21464', 'ae4466fa5f1cff66c7bbab6d'
CRED = Path.home() / '.config' / 'onshape' / 'credentials_write.json'


def auth():
    d = json.loads(CRED.read_text())
    return (d['access_key'], d['secret_key'])


def get(path, **params):
    r = requests.get(f'{B}{path}', auth=auth(), params=params, headers={'Accept': 'application/json'}, timeout=120)
    r.raise_for_status()
    return r.json()


def post(path, body=None, **kw):
    r = requests.post(f'{B}{path}', auth=auth(), json=body,
                      headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=120, **kw)
    if r.status_code >= 300:
        raise RuntimeError(f'{r.status_code} {r.text[:500]}')
    return r.json() if r.text else {}


def delete(path):
    r = requests.delete(f'{B}{path}', auth=auth(), headers={'Accept': 'application/json'}, timeout=120)
    if r.status_code >= 300:
        raise RuntimeError(f'{r.status_code} {r.text[:500]}')
    return r.json() if r.text else {}


def upload(step, name):
    """STEP als Part Studio ins Dokument übersetzen; gibt die Element-ID zurück."""
    fname = f'{name}.step'
    with open(step, 'rb') as fh:
        r = requests.post(f'{B}/blobelements/d/{DID}/w/{WID}', auth=auth(),
                          files={'file': (fname, fh, 'application/octet-stream')},
                          data={'encodedFilename': fname, 'translate': 'true', 'flattenAssemblies': 'true',
                                'yAxisIsUp': 'false', 'importInBackground': 'false', 'allowFaultyParts': 'false',
                                'unit': 'millimeter', 'createComposite': 'false', 'notifyUser': 'false'},
                          headers={'Accept': 'application/json'}, timeout=300)
    if r.status_code >= 300:
        raise RuntimeError(f'Upload {r.status_code}: {r.text[:600]}')
    info = r.json()
    blob_id = info.get('id')
    print(f"Blob-Element {blob_id} {info.get('name')!r} ({info.get('elementType')}); Import läuft …")
    # Die Übersetzung legt asynchron ein Part Studio mit dem Dateinamen an.
    before = {el['id'] for el in get(f'/documents/d/{DID}/w/{WID}/elements')} - {blob_id}
    for _ in range(90):
        time.sleep(3)
        new = [el for el in get(f'/documents/d/{DID}/w/{WID}/elements')
               if el['id'] not in before and el['id'] != blob_id and el['elementType'] == 'PARTSTUDIO']
        if new:
            print('Neues Part Studio:', [(el['id'], el['name']) for el in new])
            return [el['id'] for el in new]
    raise RuntimeError('Kein Part Studio nach dem Upload erschienen')


def elements():
    for el in get(f'/documents/d/{DID}/w/{WID}/elements'):
        print(f"  {el['id']}  [{el['elementType']}]  {el['name']}")


def parts_of(eid):
    return get(f'/parts/d/{DID}/w/{WID}/e/{eid}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'upload':
        eids = upload(sys.argv[2], sys.argv[3])
        for e in eids:
            for p in parts_of(e):
                print(f"  Part {p.get('partId')} {p.get('name')!r} in {e}")
    elif cmd == 'elements':
        elements()


# ---------------------------------------------------------------------------
# Platzierung in der Assembly
#
# Bezugsrahmen sind die beiden NorComp-Steckverbinder (Part-Studio-Koordinaten:
# Flansch-Vorderseite z = 0, Steckrichtung +z, Befestigungslöcher bei
# (2,9 | 6,3) und (36,2 | 6,3), Flansch 0,76 dick).
#   Buchse 180-026-213R001 („Extrude26"):   Clips. Der Raststift des AC-1
#     steht auf dessen Flansch (= Spitze der Buchsenschale, z = 5,84):
#     Scheibe 0,64, Sechskant 4,8, Bund 1,8 → Hals bei z = −1,40 … −2,00.
#     Gabel (0,5) mittig im Hals: Clip-z = 0 bei z = −1,45, Clip-+z = −z.
#   Stecker 180-026-113R001 („Cut-Extrude14"): Raststifte + Federscheiben
#     auf der Flansch-Vorderseite, Scheibe 0,64 unter dem Sechskant:
#     Stift-z = 0 bei z = +0,64, Gewinde (+z_Stift) = −z in den Flansch.
# ---------------------------------------------------------------------------
import numpy as np  # noqa: E402

NEW = {  # Element-IDs der übersetzten Part Studios (alle partId JFD)
    'clip': '2e89e533ed4880ec4498cb6b',
    'pin': '8441d752a53311209bfa373b',
    'washer': 'c671cac50cadd53299931941',
}
STALE_INSTANCES = ['MsOE9vRe5waq3rt50', 'METgEF1sY7GOJ5JeG', 'MKujGtkWlRpoWKmbr', 'MJ+mLcRVVfB8nlFp5']
STALE_MATES = ('Planar 6', 'Planar 7', 'Planar 8', 'Planar 9', 'Parallel 1', 'Parallel 2')
FEMALE, MALE = 'MWiSW7JWlrO7gUFtF', 'MNFdLOQguxaNnUYxR'
HOLES_F = ((2.91, 6.3), (36.23, 6.3))
HOLES_M = ((2.93, 6.3), (36.26, 6.3))
Z_CLIP, Z_PIN = -1.45, 0.64


def frame(x_axis, z_axis, origin):
    x = np.array(x_axis, float); z = np.array(z_axis, float)
    y = np.cross(z, x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, origin
    return m


def occ_matrix(t):
    m = np.array(t, float).reshape(4, 4)
    m[:3, 3] *= 1000.0            # m → mm
    return m


def to_api(m):
    out = m.copy(); out[:3, 3] /= 1000.0
    return [float(v) for v in out.reshape(-1)]


def assembly():
    return get(f'/assemblies/d/{DID}/w/{WID}/e/{AID}', includeMateFeatures='true')


def place():
    a = assembly()
    ra = a['rootAssembly']
    occ = {o['path'][0]: occ_matrix(o['transform']) for o in ra['occurrences'] if len(o['path']) == 1}
    T_F, T_M = occ[FEMALE], occ[MALE]

    # 1) veraltete Mates und Instanzen entfernen (nach jedem Löschen neu laden;
    #    ein Mate kann mit dem vorigen schon verschwunden sein → 404 tolerieren)
    for name in STALE_MATES:
        for f in assembly()['rootAssembly'].get('features', []):
            if f.get('featureData', {}).get('name') == name:
                try:
                    delete(f'/assemblies/d/{DID}/w/{WID}/e/{AID}/features/featureid/{f["id"]}')
                    print('Mate entfernt:', name)
                except RuntimeError as e:
                    print('Mate', name, 'nicht löschbar:', str(e)[:60])
    for nid in STALE_INSTANCES:
        if nid in {i['id'] for i in assembly()['rootAssembly']['instances']}:
            try:
                delete(f'/assemblies/d/{DID}/w/{WID}/e/{AID}/instance/nodeid/{nid}')
                print('Instanz entfernt:', nid)
            except RuntimeError as e:
                print('Instanz', nid, 'nicht löschbar:', str(e)[:60])

    # 2) Ziel-Lagen
    targets = []
    for i, (hx, hy) in enumerate(HOLES_F):
        outward = (-1, 0, 0) if i == 0 else (1, 0, 0)
        targets.append(('clip', T_F @ frame(outward, (0, 0, -1), (hx, hy, Z_CLIP))))
    for hx, hy in HOLES_M:
        m = T_M @ frame((1, 0, 0), (0, 0, -1), (hx, hy, Z_PIN))
        targets.append(('pin', m))
        targets.append(('washer', m))

    # 3) einfügen und setzen
    for kind, m in targets:
        before = {i['id'] for i in assembly()['rootAssembly']['instances']}
        post(f'/assemblies/d/{DID}/w/{WID}/e/{AID}/instances',
             {'documentId': DID, 'elementId': NEW[kind], 'partId': 'JFD',
              'isWholePartStudio': False, 'isAssembly': False, 'includePartTypes': ['PARTS']})
        inst = [i for i in assembly()['rootAssembly']['instances'] if i['id'] not in before]
        if len(inst) != 1:
            raise RuntimeError(f'Instanz nicht eindeutig: {inst}')
        nid = inst[0]['id']
        post(f'/assemblies/d/{DID}/w/{WID}/e/{AID}/occurrencetransforms',
             {'isRelative': False, 'occurrences': [{'path': [nid]}], 'transform': to_api(m)})
        print(f"{kind:7s} {inst[0]['name']!r} {nid}  Ursprung (mm) = {np.round(m[:3, 3], 2).tolist()}")

    # 4) Kontrolle
    ra = assembly()['rootAssembly']
    names = {i['id']: i['name'] for i in ra['instances']}
    for o in ra['occurrences']:
        if len(o['path']) == 1:
            m = occ_matrix(o['transform'])
            print(f"  {names[o['path'][0]]:40s} T={np.round(m[:3, 3], 2).tolist()} z-Achse={np.round(m[:3, 2], 3).tolist()}")


if __name__ == '__main__' and sys.argv[1] == 'place':
    place()
