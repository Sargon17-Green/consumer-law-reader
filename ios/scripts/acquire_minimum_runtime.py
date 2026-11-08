#!/usr/bin/env python3
"""Try Apple's supported CLI without credentials; report unavailable separately from tests."""
import json,os,subprocess
from pathlib import Path

BUILD=Path('build');BUILD.mkdir(exist_ok=True)
LOG=BUILD/'ios16-runtime-acquisition.log'
def installed():
    data=json.loads(subprocess.check_output(['xcrun','simctl','list','runtimes','-j']))
    return next((r for r in data['runtimes'] if r.get('version')=='16.0' and r.get('isAvailable')),None)

runtime=installed();reason=None
if not runtime:
    try:
        with LOG.open('w') as log:
            subprocess.run(['xcodebuild','-downloadPlatform','iOS','-buildVersion','16.0','-exportPath',str(BUILD/'runtime16')],stdout=log,stderr=subprocess.STDOUT,timeout=420,check=True)
        if not installed():
            for image in (BUILD/'runtime16').rglob('*.dmg'):
                with LOG.open('a') as log:
                    subprocess.run(['xcrun','simctl','runtime','add',str(image)],stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        runtime=installed()
        if not runtime:reason='Apple CLI completed but no compatible iOS 16.0 runtime became available.'
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
        reason=type(error).__name__+': '+str(error)
available=runtime is not None
report={'requestedOS':'16.0','available':available,'status':'RUNTIME_AVAILABLE'if available else'NOT_TESTED_RUNTIME_UNAVAILABLE','reason':reason,'runtime':runtime,'log':str(LOG),'scope':'SDK/runtime availability only. This probe is not an app-test PASS.'}
(BUILD/'ios16-runtime-availability.json').write_text(json.dumps(report,indent=2))
if available:
    subprocess.run(['xcrun','simctl','create','Reader Minimum iOS 16','com.apple.CoreSimulator.SimDeviceType.iPhone-14',runtime['identifier']],check=True)
with open(os.environ['GITHUB_OUTPUT'],'a') as output:output.write('available='+str(available).lower()+'\n')
print(json.dumps(report,indent=2))
