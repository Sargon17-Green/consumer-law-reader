# כניסה לפרויקט והמשך עבודה

פרויקט זה הוא **Sargon17-Green/consumer-law-reader** בלבד — קורא חוק הגנת הצרכן, התשמ״א–1981 ל־Android/iOS/Web. אין לערבב עם Pastafarian-Calendar-App. היעד הוא קורא יציב, נגיש, מאובטח וניתן להתקנה; מפרסמים ערוץ בשל בהקדם וממשיכים את היתר.

## לקרוא תחילה

1. [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md) ו־[קטלוג מובנה](docs/requirements.json): כל דרישה, קבלה, קוד, בדיקה, תלות ומצב.
2. [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md), [KNOWN_ISSUES](KNOWN_ISSUES.md), [BACKLOG](BACKLOG.md).
3. [ARCHITECTURE](ARCHITECTURE.md), [TESTING](TESTING.md), [RELEASE_PROCESS](RELEASE_PROCESS.md), [EXTERNAL_ACTIONS](EXTERNAL_ACTIONS.md).
4. [דוח שיפורים ומטריצה](docs/MOBILE_ENGINEERING_2026-11-08_HE.md), `qa/mobile-2026-11-08/` ו־[פורמט גיבוי](docs/SETTINGS_BACKUP_FORMAT_HE.md).

## מצב והפניות קבועות

- main baseline016b3de352dabe97f51b34b78ff803965b6cd40d; אין להניח שעדיין HEAD — לבדוק GitHub לפני עריכה.
- העבודה הראשית ב־**fix/pastafari-date-android-20261028**, [PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11), head הנבדק2f91d12787f37a8b75d33e3f60d8813c6ecd081d. קוד1.3.9-dev/build17. להמשיך ממנו ולא ליצור מימוש מקביל.
- ענף **release/web-reader-1.3.9-preview**, commit83fe5ec4a0d17c209088354c4ff748f63d7188a0, הוא אותו קוד Web שנבדק עם trigger פרסום נוסף. **פורסם** ב־reader/. אימות HTTP/SHA256 של74 הקבצים עבר ב־10.11.2026, כולל alpha/latest.apk; ראיה ב־qa/mobile-2026-11-08/public-web-http-verification.json.
- [CI Linux42683016176](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016176): source+4browser+build+API31 הצליחו; API26/36 נכשלו. אין PASS כולל.
- [CI iOS42683016332](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016332):4jobs הצליחו, כולל iOS16, Home Screen ו־Native audit היכן שנתמך; archive מכשיר לא חתום בלבד.
- ענף אבחון **work/mobile-android26-picker-20261109**: e50a137 list-view לא פתר; cadaa9c הוכיח pointer לפי filename bounds ב־API26 (run42685860051), ו־API36 נכשל ב־sharesheet לאחר החמרת visibility כללית. dc18fecbe3e1c726984ec9b479e561941b3d29e2 שומר visible רק ל־print_button ומחזיר אישור Intent הקודם. יש לעקוב אחרי הריצה שלו, לתקן ולהכניס רק את קוד הבדיקה הנחוץ ל־PR11. workflow האבחון אינו מוצר.
- Android ציבורי נשאר1.3.5-beta מה־[קישור הקבוע](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk); אין מפתח פרטי נגיש. iOS לא הופץ ב־TestFlight. מדיניות חתימות ו־SHA ב־RELEASE_PROCESS.

## הצעד הבא

א. פרסום Web מוקדם ואימות HTTP הושלמו. לעדכן את CI עם בדיקת ServiceWorker/cache offline אמיתי וסטטוס מוכנות המטמון. ה־deploy job של run42718069159 נדחה ב־environment; זה מתועד, ופרסום gh-pages הרגיל מאומת בנפרד. אין להסיר הגנה.

ב. להשלים full API36 online/offline ו־PDF ממשי; להכניס את תיקון Android8 (קובץ נמצא ב־AX depth17; לשורה אין ACTION_CLICK; צריך pointer בגבולות השם המדויק) ואת המתנת Print גלוי, ואז להריץ שערים על commit סופי. לא למזג שינוי שנכשל בבדיקה חיונית.

ג. לעדכן את כל המסמכים/ראיות, להכין PR למיזוג בהתאם לכללים, להמשיך בדיקות נוספות ב־BACKLOG. אין להשאיר מידע חיוני בשיחה.

## גבולות קשיחים

מקור החוק SHA256de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9; תאריך האימות2026-10-28; אין שינוי משפטי. לשמור RTL/שם מלא/נושאים/מקורות/היסטוריה/נגישות/תאריך/הדפסה/Word/שיתוף. אין ענן/חשבונות/Analytics/פרסומות. אין force-push, מפתח חתימה חלופי, החלפת APK ציבורי ב־Debug, או טענות פיזיות/חנות ללא הוכחה. אין לערבב sourceCommit של PR merge-ref עם head; משווים tree ומדווחים במפורש.

כל תיקון רגיל, בדיקה, build, אבחון, PR ופרסום שעבר את שעריו מותרים אוטונומית. מפתח פרטי/חשבון/תשלום/תנאים/מכשיר שאינו נגיש הם פעולות חיצוניות; הפרטים מרוכזים ב־EXTERNAL_ACTIONS. queued/in_progress אינם חסם או PASS. אין לחזור על ניסיון זהה ללא השערה חדשה. שיפורים ובדיקות משמעותיים נשמרים ב־GitHub בכל מחזור.
