from pathlib import Path
from html.parser import HTMLParser
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None;self.text=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in {'script','style'}:self.skip+=1
  if tag=='table': self.table=[]
  if tag=='tr' and self.table is not None: self.row=[]
  if tag in {'td','th'} and self.row is not None:self.cell=[]
 def handle_endtag(self,tag):
  if tag in {'script','style'}: self.skip=max(0,self.skip-1)
  if tag in {'td','th'} and self.cell is not None:
   self.row.append(' '.join(self.cell));self.cell=None
  if tag=='tr' and self.row is not None:
   self.table.append(self.row);self.row=None
  if tag=='table' and self.table is not None:
   self.tables.append(self.table);self.table=None
 def handle_data(self,data):
  if not self.skip and data.strip():
   self.text.append(data.strip())
   if self.cell is not None:self.cell.append(data.strip())
root=Path('experiments/bioherbicide-expansion-2026-11-12/sources')
import json
for path in root.glob('*.html'):
 p=Parser();p.feed(path.read_text())
 path.with_suffix('.txt').write_text('\n'.join(p.text))
 path.with_suffix('.tables.json').write_text(json.dumps(p.tables,indent=2)+'\n')
 print(path.name, 'tables',len(p.tables),'text',sum(map(len,p.text)))
 if path.stem in {'nonenolides2021','ambrosia2019'}:
  for i,t in enumerate(p.tables):print(i,str(t)[:5000])
