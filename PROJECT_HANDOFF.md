# כניסה לפרויקט והמשך עבודה

פרויקט זה הוא **Sargon17-Green/consumer-law-reader** בלבד — קורא חוק הגנת הצרכן, התשמ״א–1981 ל־Android/iOS/Web. אין לערבב עם Pastafarian-Calendar-App. היעד הוא קורא יציב, נגיש, מאובטח וניתן להתקנה; מפרסמים ערוץ בשל בהקדם וממשיכים את היתר.

## לקרוא תחילה

1. [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md) ו־[קטלוג מובנה](docs/requirements.json): כל דרישה, קבלה, קוד, בדיקה, תלות ומצב.
2. [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md), [KNOWN_ISSUES](KNOWN_ISSUES.md), [BACKLOG](BACKLOG.md).
3. [ARCHITECTURE](ARCHITECTURE.md), [TESTING](TESTING.md), [RELEASE_PROCESS](RELEASE_PROCESS.md), [EXTERNAL_ACTIONS](EXTERNAL_ACTIONS.md).
4. [דוח שיפורים ומטריצה](docs/MOBILE_ENGINEERING_2026-11-08_HE.md), `qa/mobile-2026-11-08/` ו־[פורמט גיבוי](docs/SETTINGS_BACKUP_FORMAT_HE.md).

## מצב והפניות קבועות

- main baseline016b3de352dabe97f51b34b78ff803965b6cd40d; לרענן head/PR/runs מ־GitHub לפני עריכה.
- העבודה הראשית **fix/pastafari-date-android-20261028**, [PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11), קוד1.3.9-dev/build17. ממשיכים ממנה. commit4ee85a3 נבדק ב־merge46d170c עם tree זהה7578188ec14ef4421f70bcb177cd90c0fd698a22.
- **Web פורסם** מתוך release/web-reader-1.3.9-preview/source83fe5ec4a0d17c209088354c4ff748f63d7188a0. [reader](https://sargon17-green.github.io/consumer-law-reader/reader/) תומך הוספה למסך הבית. Pages42718136476 success;74GET/SHA256 עברו כולל alpha/latest.apk. ראיה: [HTTP](qa/mobile-2026-11-08/public-web-http-verification.json).
- [Linux42721600913](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42721600913): source+4browser+build+Android26/31 הצליחו; **Android36 נכשל ב־PDF**. אין PASS כולל.
- [iOS42721601016](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42721601016): כל4jobs הצליחו, כולל iOS16, iPad, Home Screen ו־Native audit היכן שנתמך; device archive לא חתום. [סיכום קבוע](qa/mobile-2026-11-08/acceptance-4ee85a3.json).
- אבחון work/mobile-print-lifecycle-20261110/e120c5dd75fa0710f399af03815c6bce1eb86e17: [run42726433709](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42726433709) landscape עבר לאחר המתנה לעמוד preview: PDF146עמודים/1,515,150bytes, hash בדוח. portrait נכשל; fatal ראשון ב־system MediaProvider/FuseDaemon, ואז יציאת reader instrumentation. אין הוכחת סיבת שורש באפליקציה. [אבחון וארטיפקטים](qa/mobile-2026-11-08/android-print-preview-diagnosis.json). lifecycle resume/orientation בלבד לא פתרו; אין לשנות production על בסיס זה. workflow האבחון אינו מוצר.
- Android ציבורי נשאר1.3.5-beta מה־[קישור הקבוע](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk); אין מפתח פרטי נגיש. iOS לא הופץ ב־TestFlight. פרטי זהויות וחתימות ב־RELEASE_PROCESS.

## הצעד הבא

א. לקבל ולפרסם בנפרד את תיקוני Web NAV-006/PWA-001/CI-003 שבמחזור הנוכחי. אין להמתין ל־Native. תיקון cache נבדק מול מחיקת CSS והוספת נכס זר ללא שינוי ספירה. fixture משותף בודק כל66 התקנות ×4גדלי גופן, כולל מיקום יעדים מתחת לחזרה. לדרוש CI completed ו־HTTP כולל owner marker לפני פרסום. legacy verifier אינו deployment ואין לשנות environment protection.

ב. להריץ full API26/31/36 עם המתנת preview שנלקחה מאבחון e120. להשאיר אישור Intent ב־UID אחר, SAF/PdfRenderer והחזרה ל־reader. לא למחוק בדיקה כושלת או לסמן run חלקי כ־PASS. Android26 filename-depth17 נפתר כבר ב־4ee באמצעות pointer מדוד; אין ליישמו שוב.

ג. לעדכן קטלוג60 הדרישות, מצב/ראיות/פרסום והעברה לאחר כל מחזור. להמשיך iPad window/low memory לפי BACKLOG. אין למזג כשל מהותי; pending אינו חסם. אין צורך בחבילת Windows.

## גבולות קשיחים

מקור החוק SHA256de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9; תאריך האימות2026-10-28; אין שינוי משפטי. לשמור RTL/שם מלא/נושאים/מקורות/היסטוריה/נגישות/תאריך/הדפסה/Word/שיתוף. אין ענן/חשבונות/Analytics/פרסומות. אין force-push, מפתח חתימה חלופי, החלפת APK ציבורי ב־Debug, או טענות פיזיות/חנות ללא הוכחה. אין לערבב sourceCommit של PR merge-ref עם head; משווים tree ומדווחים במפורש.

כל תיקון רגיל, בדיקה, build, אבחון, PR ופרסום שעבר את שעריו מותרים אוטונומית. מפתח פרטי/חשבון/תשלום/תנאים/מכשיר שאינו נגיש הם פעולות חיצוניות; הפרטים מרוכזים ב־EXTERNAL_ACTIONS. queued/in_progress אינם חסם או PASS. אין לחזור על ניסיון זהה ללא השערה חדשה. שיפורים ובדיקות משמעותיים נשמרים ב־GitHub בכל מחזור.
