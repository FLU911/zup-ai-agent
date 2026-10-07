import sys, zipfile, re, xml.etree.ElementTree as ET
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
p=sys.argv[1]
z=zipfile.ZipFile(p)
shared=[]
if 'xl/sharedStrings.xml' in z.namelist():
    r=ET.fromstring(z.read('xl/sharedStrings.xml'))
    for si in r.findall('m:si',NS):
        shared.append(''.join(t.text or '' for t in si.iter('{%s}t'%NS['m'])))
sheet=[n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml$',n)][0]
r=ET.fromstring(z.read(sheet))
for row in r.iter('{%s}row'%NS['m']):
    cells=[]
    for c in row.findall('m:c',NS):
        v=c.find('m:v',NS); t=c.get('t')
        if v is None:
            isel=c.find('m:is',NS)
            val=''.join(x.text or '' for x in isel.iter('{%s}t'%NS['m'])) if isel is not None else ''
        elif t=='s': val=shared[int(v.text)]
        else: val=v.text or ''
        val=val.strip()
        if val: cells.append(val)
    if cells: print(' | '.join(cells))
