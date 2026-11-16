from pathlib import Path
import ast,json
# Reuse only the table parser, avoiding that script's acquisition-specific top-level loop.
p=Path('experiments/bioherbicide-expansion-2026-11-12/inspect_html.py')
module=ast.parse(p.read_text()); keep=[n for n in module.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef))]
ns={};exec(compile(ast.Module(body=keep,type_ignores=[]),str(p),'exec'),ns)
for path in (Path(__file__).parent/'sources').glob('*.html'):
 parser=ns['Parser']();parser.feed(path.read_text())
 path.with_suffix('.txt').write_text('\n'.join(parser.text))
 path.with_suffix('.tables.json').write_text(json.dumps(parser.tables,indent=2)+'\n')
 print(path.name,len(parser.tables))
 for i,t in enumerate(parser.tables):
  if path.stem!='prestwick2025':print(i,json.dumps(t)[:18000])
