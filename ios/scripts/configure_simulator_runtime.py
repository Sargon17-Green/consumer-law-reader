#!/usr/bin/env python3
"""Apply Apple's simulator-only Swift WebKit overlay workaround, preserving iOS 16 support.
https://developer.apple.com/forums/thread/785964
No library is packaged, copied or substituted in the distribution app.
"""
from pathlib import Path
import json,subprocess,sys,xml.etree.ElementTree as ET
identifier=sys.argv[1]
devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','available','-j']))['devices']
runtime_id=next(key for key,values in devices.items()if any(x['udid']==identifier for x in values))
runtimes=json.loads(subprocess.check_output(['xcrun','simctl','list','runtimes','-j']))['runtimes']
runtime=next(x for x in runtimes if x['identifier']==runtime_id)
base=Path(runtime['bundlePath'])/'Contents/Resources/RuntimeRoot'
candidates=[base/'System/Cryptexes/OS/usr/lib/swift',base/'usr/lib/swift']
folder=next((x for x in candidates if (x/'libswiftWebKit.dylib').is_file()),None)
scheme=Path('ios/ConsumerLawReader.xcodeproj/xcshareddata/xcschemes/ConsumerLawReader.xcscheme')
if folder:
    tree=ET.parse(scheme)
    for action in tree.getroot():
        if action.tag not in ('TestAction','LaunchAction'):continue
        env=action.find('EnvironmentVariables')
        if env is None:env=ET.SubElement(action,'EnvironmentVariables')
        for prior in list(env):
            if prior.get('key')=='DYLD_FALLBACK_LIBRARY_PATH':env.remove(prior)
        ET.SubElement(env,'EnvironmentVariable',key='DYLD_FALLBACK_LIBRARY_PATH',value=str(folder),isEnabled='YES')
    tree.write(scheme,encoding='utf-8',xml_declaration=True)
print(json.dumps({'device':identifier,'runtime':runtime['name'],'version':runtime['version'],'swiftOverlayFallback':str(folder)if folder else None}))
