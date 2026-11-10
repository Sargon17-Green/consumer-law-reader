# החלטות תכנון ותפעול

| מזהה | החלטה ונימוק | השלכה / תנאי חזרה |
|---|---|---|
| DEC-001 | מקור החוק נשמר בביטים; כל תיקון טכנולוגי בתצוגה/ניווט | SHA/DOM guard חובה; אין שינוי הערות/תוקף/תאריך אימות |
| DEC-002 | ממשק משותף עם מעטפות Native לפעולות מערכת | אין שכתוב כולל/SDK ענן; Native SAF/Files/Share/Print |
| DEC-003 | מנוע נרמול יחיד עם mapping UTF-16; אינדקס מהיר ומיפוי רק snippets | ניסוי TreeWalker ואינדקס mapping מלא לא התקבלו לאחר רגרסיית ביצועים; אין לשחזרם בלי מדידה |
| DEC-004 | backup schema2 עם whitelist ויומן rollback | אין סנכרון ענן; אין שכתוב של נתונים מחוץ לתחום |
| DEC-005 | תאריך הוא נתון JSON ולא סקריפט צד שלישי | שלוש כתובות מדויקות; fallback בלי שינוי האלגוריתם הקנוני |
| DEC-006 | פרוזה ממוספרת מתלפפת; טפסים/נתונים נשארים דו־ממדיים באזור גלילה | אין הסתרת overflow כתחליף לתיקון ואין שינוי במקור או בסמנטיקה המשפטית |
| DEC-007 | שומרים alpha הקיים בשורש, מפרסמים reader/ בנפרד | אין החלפה של המקור הישן באלפא ואין שבירת הורדת APK |
| DEC-008 | מפתח שדרוג Android נשאר מקורי; QA נפרד וגלוי | לא יוצרים מפתח חלופי ולא משנים package ID כדי להתחזות להפצה |
| DEC-009 | iOS16 נבדק עם runtime רשמי שנרכש אוטומטית | אין תירוץ של חוסר חשבון לרכישת simulator; workaround CI מתועד ואינו פטור מהבדיקה |
| DEC-010 | Android8 CI עם AOSP WebView133 ו־RRO משאב יחיד, SELinux enforcing | סביבה מותאמת מתועדת; אין טענה לתמונת retail או מכשיר פיזי |
| DEC-011 | אין Native Universal/App Links בלי פרטי בעלות/חתימה מאומתים; HTTPS עובד | custom scheme לא הוסף רק להגדלת היקף; חוזרים כשיש ערך ובעלות |
| DEC-012 | מפרסמים מוקדם כל פלטפורמה שעברה שערים, בלי המתנה לפלטפורמה אחרת | מאז10.11.2026; כשל Native נשאר גלוי אך אינו מעכב Web נבדק; אין הסרת שער חיוני |
| DEC-013 | לא עוקפים env/branch protection; פרסום רק במסלול שמותר במדיניות | release branch אינו מותר ל־github-pages; אין להחליש policy כדי להפוך run לירוק |
| DEC-014 | ידע הפרויקט במאגר בלבד: קטלוג דרישות, מצב, ראיות, backlog/handoff | אין תלות בשיחה; כל מחזור מעדכן הקשרים ומספרי commit אמיתיים |
| DEC-015 | אין ניסיונות CI זהים ללא השערה חדשה; pending אינו חסם | max-parallel2 בעקבות GitHub500 שמנע יצירת jobs; רק completed/log מוכיחים PASS |

| DEC-016 | מוכנות offline דורשת את כל שמות נכסי החובה, ולא ספירת רשומות; מוצגת מתוך worker שולט בלבד | כשל/timeout מוצגים בלי לחסום קריאה; מטמון פגום אינו מסומן מוכן |
| DEC-017 | יישור יעד תקנות נעשה אחרי focus, עם מדידת כפתור החזרה בפועל | focus עשוי להזיז scroller גם עם preventScroll; אין hardcoded offset או שינוי מקור |
| DEC-018 | legacy Pages נפרס במסלול gh-pages הקיים; job נוסף מאמת GET בלבד | אין בקשת deployment מ־release branch ואין החלשת environment; workflow-mode ממשיך לדרוש אותו |
| DEC-019 | PDF QA ממתין ל־Page n of total ומקיש לפי bounds מדודים | lifecycle/orientation לבדם הופרכו בניסוי; אין שינוי production onPause ללא ראיה |

המאגר ציבורי מלכתחילה. אין שינוי פרטיות, רכישות, קבלת תנאים, סודות או force-push במחזור זה. המלצות Apple/Google נבדקות במקורות הרשמיים המופנים ב־docs/STORE_PREPARATION_HE.md. התקן לחבילות Windows נמצא מחוץ למאגר; אין ליצור חבילה כזו בלי לקרוא את הגרסה הקנונית המלאה. כרגע אין צורך בחבילת Windows.

CI-004: רשימות קלט iOS זהות ב־push וב־pull_request, כולל fixture שמשמש את WKWebView ותלויות Python. רשימת build scripts משותפים מפורשת; כלי Android בלבד אינם מפעילים macOS. יש לעדכן רשימה כאשר מוסיפים תלות build חדשה.

## Android transient state cache — DATA-003

The06/API36fatal proves the fullWebViewBundle cannot travel through Binder. Preserve the opaque fullhistory in privateAtomicFile cache; systemstate contains onlyUUID+SHA. Parcel is deliberately treated as transient: exactOSfingerprint/appinstallation/providerinstallation signature and format/digest/size checks invalidate incompatible bytes. Missing/corrupt/evicted cache reopens the bundled law and durablelogicalsession; settings are never removed. This avoids discarding workingBack/Forward merely to reduceBundle size. No newpermission, dependency, externalstore or cloud service.


## קיבוע XcodeGen באותו כלי שנמדד

ריצות iOS מ־10.11 תיעדו XcodeGen2.46.0, אך `brew install xcodegen` לא קיבע גרסה. CI משתמש כעת ב־[נכס הרשמי2.46.0](https://github.com/yonaskolb/XcodeGen/releases/tag/2.46.0), ארכיון4,278,764בתים עם SHA256 `4d9e34b62172d645eed6457cac13fc222569974098ef4ee9c3368bedf0196806`, שאומת גם בהורדה עצמאית. הבינרי וה־SettingPresets נפרסים תחת RUNNER_TEMP, והגרסה נרשמת בדוח הסביבה. אין התקנה מערכתית חדשה. archive_for_testflight דורש אותה גרסה; ב־94 כל חמש הסביבות בנו עם הבינרי המקובע; שלושה jobs עברו ושני מבחני UI נכשלו בסגירת השיתוף. נדרשת קבלה מלאה למועמד הבא.

לבדיקת מקלדת Android מודדים חלון מערכת מסוג TYPE_INPUT_METHOD, מגע ב־editable node, הקלדה native וגבולות WebView; אין להסיק כיסוי IME משינוי CSS בלבד. [תיעוד Android](https://developer.android.com/develop/ui/views/layout/sw-keyboard) ו־[AccessibilityWindowInfo](https://developer.android.com/reference/android/view/accessibility/AccessibilityWindowInfo) נבדקו. בדיקת QA משנה זמנית show_ime_with_hard_keyboard ומשחזרת את ערכה ואת orientation/דגלי השירות ב־finally.

ניסוי חומרה מצומצמת דורש מדידה מתוך מערכת האורח לפני הבדיקה: ניסיון1GB נדחה משום שהאמולטור כפה1.5GB. ב־42819646591 התקבלו בפועל MemTotal1548780KB וליבה אחת, והמבחנים online/offline עברו. אין להציג ערכי CLI כמדידה או לייחס זאת ל־OOM/מכשיר פיזי.
