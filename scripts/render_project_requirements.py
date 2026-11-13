#!/usr/bin/env python3
"""Render the single requirements catalog without changing its state."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def render(data):
    lines=['# דרישות המוצר — חוק הגנת הצרכן','', 'מקור האמת המובנה הוא [docs/requirements.json](docs/requirements.json). טבלה זו נגזרת ממנו באמצעות scripts/render_project_requirements.py; אין לערוך בה מצב בנפרד. מימוש, אימות ופרסום הם מצבים שונים. כל ראיה מוגבלת לסביבה ולתרחיש המתועדים.','', 'אין במסגרת מחזור זה בדיקה משפטית של נוסח החקיקה. LAW-001 מחייב בכל מהדורה. מאז10.11.2026 מפרסמים ערוץ בשל מוקדם, ממשיכים את היתר ושומרים את כל הידע במאגר.','', '| מזהה | דרישה וקריטריוני קבלה | פלטפורמה ומצב | קוד | בדיקות / ראיות | תלות / פרסום |','|---|---|---|---|---|---|']
    links=lambda paths:'<br>'.join('['+p+']('+p+')' for p in paths) or '—'
    for row in data['requirements']:
        state='<br>'.join(p+': '+v for p,v in row['status'].items())
        evidence='<br>'.join('[run '+str(e['run'])+']('+e['url']+') — '+e['result'] for e in row['evidence'])
        released='<br>'.join(p+': '+(str(v['version'])+' · '+v['url'] if v else 'לא פורסמה מהדורת המועמד') for p,v in row['published'].items())
        fields=[row['id'],'**'+row['title']+'**<br>'+'<br>'.join(row['acceptance']),state,links(row['implementation']),links(row['tests'])+('<br>'+evidence if evidence else ''),'<br>'.join(row['dependencies'])+'<br>'+released]
        lines.append('| '+' | '.join(f.replace('|','&#124;') for f in fields)+' |')
    return '\n'.join(lines)+'\n'
if __name__=='__main__':
    data=json.loads((ROOT/'docs/requirements.json').read_text())
    (ROOT/'PRODUCT_REQUIREMENTS.md').write_text(render(data))
    print('Rendered',len(data['requirements']),'requirements')
