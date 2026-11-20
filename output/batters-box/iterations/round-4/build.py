style = open('_style.txt').read()

EXTRA = """
<style>
/* content pages: prose, ruled cell grids, a results table */
.prose { max-width: 66ch; }
.prose p { color: var(--muted); }
.prose strong { color: var(--text); font-weight: 600; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.92em; color: var(--chalk); }
h2.sub { font-family: var(--display); font-weight: 700; font-size: 26px; margin: var(--s5) 0 var(--s3); }

.cells { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: var(--rule); border: 1px solid var(--rule); }
.cells.three { grid-template-columns: repeat(3, 1fr); }   /* 6 cells, 2 full rows, no orphan track */
@media (max-width: 900px) { .cells.three { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .cells, .cells.three { grid-template-columns: 1fr; } }
.cell { background: var(--panel); padding: var(--s4); }
.cell h3 { font-family: var(--display); font-weight: 700; font-size: 20px; margin: 0 0 var(--s2); }
.cell .tag { font-family: var(--display); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); display: block; margin-bottom: var(--s1); }
.cell p { margin: 0; color: var(--muted); font-size: 14px; }

table.rt { width: 100%; border-collapse: collapse; border: 1px solid var(--rule); font-variant-numeric: tabular-nums; }
table.rt caption { text-align: left; font-family: var(--display); font-size: 13px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); padding-bottom: var(--s2); }
table.rt th, table.rt td { padding: 9px 14px; border-bottom: 1px solid var(--rule); text-align: right; font-size: 14px; }
table.rt th { font-family: var(--display); font-weight: 600; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }
table.rt th:first-child, table.rt td:first-child { text-align: left; }
table.rt tbody tr:nth-child(even) { background: var(--panel-2); }
table.rt tbody tr:last-child td { border-bottom: none; }
table.rt .best { color: var(--accent); font-weight: 600; }

.hh { display: grid; grid-template-columns: 1fr auto 1fr; border: 1px solid var(--rule); margin-bottom: var(--s4); }
.hh .pick { background: var(--panel); padding: var(--s4); }
.hh .pick-head { display: flex; align-items: center; gap: var(--s3); margin-bottom: var(--s3); }
.hh .pick-head img { width: 40px; height: 40px; object-fit: contain; flex: none; }
.hh .pick-head .nm { font-family: var(--display); font-weight: 700; font-size: 24px; line-height: 1; }
.hh .mid { background: var(--panel); border-left: 1px solid var(--rule); border-right: 1px solid var(--rule); padding: var(--s4); display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: 210px; }
.hh .series { font-family: var(--display); font-weight: 700; font-size: 46px; line-height: 1; font-variant-numeric: tabular-nums; }
.hh .series-k { font-family: var(--display); font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: var(--muted); }
.hh .diff { color: var(--muted); font-size: 14px; margin-top: var(--s1); }
.hh .note { font-size: 13px; color: var(--muted); margin-top: var(--s2); }

.games { border: 1px solid var(--rule); }
.game { display: grid; grid-template-columns: 110px 1fr auto 70px; gap: var(--s4); align-items: center; padding: 10px var(--s4); background: var(--panel); font-size: 14px; }
.game .fx { display: flex; align-items: center; gap: var(--s2); }
.game .fx img { width: 18px; height: 18px; object-fit: contain; flex: none; }
.game:nth-child(even) { background: var(--panel-2); }
.game + .game { border-top: 1px solid var(--rule); }
.game .d { font-family: var(--display); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-size: 13px; }
.game .score { font-family: var(--display); font-weight: 700; font-size: 20px; font-variant-numeric: tabular-nums; }
.game .w { font-family: var(--display); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; text-align: right; }
.game .w.away { color: var(--away); }   /* the left picker's team */
.game .w.home { color: var(--home); }   /* the right picker's team */

.callout { border-left: 2px solid var(--accent); background: var(--panel); padding: var(--s3) var(--s4); margin: var(--s4) 0; }
.callout p { margin: 0; color: var(--muted); font-size: 14px; }
.callout strong { color: var(--text); font-weight: 600; }
@media (max-width: 560px) {
  /* right-aligned cells read badly once the text wraps to three lines */
  table.rt th, table.rt td { text-align: left; padding: 8px 10px; }
}
@media (max-width: 820px) {
  .hh { grid-template-columns: 1fr; }
  .hh .mid { border-left: none; border-right: none; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); }
  .game { grid-template-columns: 90px 1fr auto; }
  .game .w { grid-column: 2 / -1; text-align: left; }
}
</style>
"""

NAV = ['predictions','players','teams','model','matchups','about']
LABEL = {'predictions':'Predictions','players':'Players','teams':'Teams',
         'model':'Model','matchups':'Matchups','about':'About'}
CUR = ' aria-current="page"'

def page(slug, title, main):
    links = []
    for s in NAV:
        cur = CUR if s == slug else ''
        links.append('<a href="#' + s + '"' + cur + '>' + LABEL[s] + '</a>')
    nav = '\n      '.join(links)
    return ('<!doctype html>\n<html lang="en" data-type="software" data-radius="sharp">\n<head>\n'
      '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
      '<meta name="page-type" content="software">\n<meta name="site-kind" content="software">\n'
      '<title>' + title + ' — Full Count</title>\n'
      '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
      '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">\n'
      + style + EXTRA + '</head>\n<body>\n'
      '<header class="topbar">\n  <div class="wrap">\n    <a class="mark" href="#home">Full Count</a>\n'
      '    <nav class="sections">\n      ' + nav + '\n    </nav>\n  </div>\n</header>\n'
      '<div class="wrap">\n' + main + '\n</div>\n'
      '<footer>\n  <div class="wrap"><p>Stats from the MLB Stats API, Baseball-Reference and Baseball Savant. Season to date.</p></div>\n</footer>\n'
      '</body>\n</html>\n')

exec(open('content.py').read())
open('model.html','w').write(page('model','Model',MODEL))
open('matchups.html','w').write(page('matchups','Matchups',MATCHUPS))
open('about.html','w').write(page('about','About the data',ABOUT))
print('written')
