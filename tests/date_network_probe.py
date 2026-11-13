"""Observe upstream freshness for native online QA, without calculating a calendar."""
from urllib.request import urlopen,Request
from datetime import datetime,timezone
from pathlib import Path
import json
URL='https://raw.githubusercontent.com/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json'
report={'url':URL,'fresh':False}
try:
 with urlopen(Request(URL,headers={'Accept':'application/json'}),timeout=20)as response:
  data=json.loads(response.read(262145))
  now=datetime.now(timezone.utc)
  ages=[(now-datetime.fromisoformat(t.replace('Z','+00:00'))).total_seconds() for t in (data['calculationAt'],data['cacheMeta']['fetchedAt'])]
  report.update(status=response.status,calculationAt=data['calculationAt'],fresh=data['cacheMeta']['mode']=='automated-seer-snapshot' and all(-300<=age<=26*3600 for age in ages))
except Exception as error:report['error']=str(error)
Path('evidence').mkdir(exist_ok=True);Path('evidence/date-upstream.json').write_text(json.dumps(report,indent=2))
print('true'if report['fresh']else'false')
