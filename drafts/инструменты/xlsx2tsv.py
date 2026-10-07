# -*- coding: utf-8 -*-
"""xlsx -> TSV с СОХРАНЕНИЕМ номеров колонок (пустые ячейки не схлопываются)."""
import sys, zipfile, re, xml.etree.ElementTree as ET
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def col_idx(ref):
    m=re.match(r'([A-Z]+)',ref or ''); 
    if not m: return None
    n=0
    for ch in m.group(1): n=n*26+ord(ch)-64
    return n-1
z=zipfile.ZipFile(sys.argv[1])
shared=[]
if 'xl/sharedStrings.xml' in z.namelist():
    r=ET.fromstring(z.read('xl/sharedStrings.xml'))
    for si in r.findall('m:si',NS):
        shared.append(''.join(t.text or '' for t in si.iter('{%s}t'%NS['m'])))
sheet=sorted(n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml$',n))[0]
r=ET.fromstring(z.read(sheet))
out=[]
for row in r.iter('{%s}row'%NS['m']):
    cells={}
    for c in row.findall('m:c',NS):
        i=col_idx(c.get('r'))
        if i is None: continue
        v=c.find('m:v',NS); t=c.get('t')
        if v is None:
            isel=c.find('m:is',NS)
            val=''.join(x.text or '' for x in isel.iter('{%s}t'%NS['m'])) if isel is not None else ''
        elif t=='s': val=shared[int(v.text)]
        else: val=v.text or ''
        val=(val or '').replace('\t',' ').replace('\n',' ').strip()
        if val: cells[i]=val
    out.append(cells)
w=max([max(c)+1 for c in out if c] or [0])
for cells in out:
    line=[cells.get(i,'') for i in range(w)]
    if any(line): sys.stdout.write('\t'.join(line)+'\n')
