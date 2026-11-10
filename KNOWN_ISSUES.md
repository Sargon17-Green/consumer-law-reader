# תקלות ידועות ומגבלות כיסוי

עודכן ב־10.11.2026. מצב מימוש/אימות/פרסום ב־[IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md); כל דרישה פתוחה ב־[BACKLOG](BACKLOG.md).

| מזהה | מצב | ממצא ודרך המשך |
|---|---|---|
| QA-IOS-LEGACY-SHARE | קבלה אוטומטית פתוחה | iPhone16/iPad18.5 במועמד94 נכשלו בדרישת היעלמותActivityListView. swipe כללי לא סגר; Close של26 אינו identifier נייד. ניסויClose נגיש מתוך החלון רץ בענףwork/ios-legacy-share-20261110. אין להסיר את בדיקת ההיעלמות |
| DATA-003 / Issue14 | Android94 עבר; סגירתIssue מחכה למועמד הסופי | ב־06/36 קרס Binder ב־Activity state1,204,952bytes. ב־94 כלAPI26/31/36 עברו online/offline עםraw1.6MB→Activity1036–1200bytes, recreate/history והקלטים העוינים. [לפני](qa/mobile-2026-11-08/android-binder-state-before.json), [אחרי](qa/mobile-2026-11-08/acceptance-94cdf7d.json) |
| NATIVE-003 / Issue13 | iPad26/94 עבר במלואו | scaling ו־SystemClose overlap תוקנו;1032→375pt/44pt/תפריט/שיתוף/סגירה/תוצאה נראית ושאילתה עברו במערכת בפועל. סגירתIssue אחרי קבלה משולבת; אין לבלבל עם כשל השיתוף במערכות הישנות. [ראיה](qa/mobile-2026-11-08/ipad-window-94cdf7d.json) |
| QA-ANDROID36-PRINT | PDF146עמודים עבר | כשל MediaProvider/FUSE היסטורי נפרד מ־Binder; סיבתpf_setattr לא הוכחה. collectorפרטיuserdebug/UID0/SELinuxEnforcing מאמתstat/magic/גודל/SHA, בליdebuggable. חמשת קובצי94 אומתו עצמאית; ה־PDF אינוtagged. [ראיה](qa/mobile-2026-11-08/android-private-exports-94cdf7d.json) |
| NATIVE-002 | Android IME עבר; תחום מוגבל | מגע/הקלדה/חלוןIME/גבולות/Back אמיתיים עברו26/31/36 בשני מצבי רשת. אין כיסוי לכלcutout/מקלדת/טאבלט; ב־iOStyping/rotation אינו בדיקת גבולותIME מקיפה |
| COVERAGE-LOW-MEMORY | חלקי ומדוד | Android26 עבר1.5GB/ליבה אחת. renderer recovery אמיתי31/36 עבר. אין טענת1GB,OOM או לחץזיכרון ממושך/כלל תהליכיWeb. [תצורה](qa/mobile-2026-11-08/android-constrained-hardware.json) |
| COVERAGE-PHYSICAL | לא נבדק | מכשירים פיזיים, בדיקות אדםVoiceOver/TalkBack, מדפסת פיזית ורינדור בקוראWord חיצוני |
| SIGN-ANDROID | גישה חיצונית חסרה | לא אומת מפתח פרטי מקורי נגיש בחיפוש הממוקד; הציבורי1.3.5 נשמר. איןDebug כשדרוג. [תחום החיפוש](qa/mobile-2026-11-08/signing-availability-scope.json) |
| SIGN-IOS | גישה חיצונית חסרה | איןTeam/profiles/ASC מורשים; סימולטור ו־unsignedarchive בלבד |
| LINKS-NATIVE | הבדל מתועד | HTTPS מוביל לסעיףב־Web; איןUniversal/AppLinks מאומתים ל־Native |
| DEPLOY-ENVIRONMENT | חוזה פרסום | github-pages מתירmain/gh-pages. verifier בענףrelease הואGET בלבד. אין לעקוףהגנה |

הגלילה הלא מכוונת שוחזרה ותוקנה:64/35/32/17/3/6 כשליroot בששת הרוחבים לפני,0 בכל רוחב אחרי. טבלאות רחבות שומרות גלילה פנימית נגישה. [ראיה](qa/mobile-2026-11-08/horizontal-layout-before-after.json).

SEARCH-005 פורסם ב־Web תיקון3 ועבר5רצפיDOM. ב־94 עברו גםAndroidוחזרתiPad26; אין צורך בפרסוםWebזהה. [פרסום](qa/mobile-2026-11-08/public-web-patch3-http-verification.json), [זהות38נכסי94](qa/mobile-2026-11-08/source-94cdf7d.json).

אין להסיר רגרסיותSAF26/filename/depth17 או cross-UIDshare36 כדי לקצר ריצה. ארטיפקטיActions מוגבלים בזמן (iOS7ימים,רובהאחרים30,פריסה90); מזהים/גיבובים וסיכומים נשמריםב־Git. היעלמותartifact אינהPASS או כשלחדש. המקור המשפטי ומועד אימותו נשמרים; הבדיקות אינן אימותמשפטי או אישורנגישות כולל.
