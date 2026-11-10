# מצב מימוש, אימות ופרסום

עודכן ב־10.11.2026. [קטלוג 63 הדרישות](docs/requirements.json) הוא מקור המצב המובנה; PRODUCT_REQUIREMENTS נגזר ממנו. מימוש, אימות ופרסום נבדלים. אין קבלה לפי קוד קיים או CI ממתין.

| ערוץ | מצב מאומת | פרסום בפועל |
|---|---|---|
| Web/PWA 1.3.9-dev, תיקון3 | במועמד94 עברו52 יחידות,35 SHA/DOM, Node500,5 רצפי חיפוש,4 רוחבים,32 סריקות axe ומטמון offline;38 נכסי runtime זהים לפרסום | [reader](https://sargon17-green.github.io/consumer-law-reader/reader/), מקור cca785ed8b1f3d4c96bf25c0eb50e77b04899566, מטמון453decfde812ec9b. פרסום42778620385 הצליח;75 GET/SHA מאומתים ושימור alpha/APK |
| Android 1.3.9-dev/code17 | כל9 משימות Linux/Android של94 עברו, כולל API26/31/36 online/offline, IME אמיתי, cache עוין, renderer31/36, SAF/PDF ושדרוג בזהות QA | הציבורי נשאר1.3.5-beta בחתימה המקורית; מועמד חדש Debug/unsigned בלבד |
| iOS 1.3.9/build17 | ב־94 עברו iPhone26.2/18.5 ו־iPad26.2. iPad26 עבר שינוי חלון אמיתי375pt/פקדים44pt/תפריט/שיתוף/חזרה. iPhone16 ו־iPad18.5 נכשלו בסגירת השיתוף | סימולטורים וארכיון מכשיר לא חתום בלבד; אין IPA חתום או TestFlight |

## קבלה משולבת

המועמד `94cdf7d260372361919d9b3eca74393ee02cde6f`, tree `7cf04c1127e22318f70a36a816c40418b44b3bf7`, נבדק ב־PR checkout `60a5c79bfc281384f4256f6ee592d0b2d67beb14` בעל אותו tree. [Linux42817834059](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42817834059) הסתיים **9/9 PASS**; [iOS42817834181](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42817834181) הסתיים **3/5 PASS,2 FAIL**. [ראיה](qa/mobile-2026-11-08/acceptance-94cdf7d.json). אין קבלה כוללת או מיזוג למועמד שנכשל.

בשני הכשלים נדרש ActivityListView להיעלם לפני סיבוב והפעלה מחדש. הבדיקה חיפשה identifier של26 ואז swipe כללי שלא סגר את השיתוף במערכות הישנות. ניסוי `work/ios-legacy-share-20261110` בודק Close נגיש בפועל. אחרי קבלתו מעבירים רק את הבדיקה הקבועה ל־PR11 ומריצים שוב את מלוא14 השערים על tree אחד; workflow האבחון אינו מועבר. כשל קומפילציה בניסוי51f תוקן ב־5450373 ואינו PASS.

הקבלה ההיסטורית המלאה האחרונה היא706a3bc: [Linux](qa/mobile-2026-11-08/acceptance-706a3bc-linux.json), [iOS](qa/mobile-2026-11-08/acceptance-706a3bc-ios.json). היא אינה מכסה קוד מאוחר. [כשל06](qa/mobile-2026-11-08/acceptance-06e5533.json) נשמר; רגרסיות Binder ו־iPad שלו עברו ב־94 בהיקף המפורט.

## תיקונים וגבולות הראיה

- **DATA-003 / Issue14:** AtomicFile פרטי והפניית UUID:SHA ב־Bundle. ב־94 נמדדו raw Chromium1,615,960–1,617,964bytes לעומת Activity1,036–1,200bytes. עברו recreate/history/Back/Forward, hash ישן, payload משובש, זהות התקנה וגבולות8MB בכל3API בשני מצבי הרשת. [ראיה](qa/mobile-2026-11-08/acceptance-94cdf7d.json).
- **NATIVE-001:** Ready מוגבל20שניות עם generation. עצירת renderer אמיתית והתאוששות עם סעיף14/גופן24/שאילתה14 עברו31/36. הפעולה הציבורית אינה זמינה26 ואינה מסומנת PASS.
- **NATIVE-002 Android:** מגע ב־editable, הקלדת Native, חלון IME נצפה, WebView ושדה מעל המקלדת, ו־Back השומר חיפוש עברו בכל3API online/offline. אין ייחוס CSS למקלדת Native.
- **NATIVE-003 / Issue13:** orientations תיקנו scaling; containerCornerOffset של26 מונע חפיפת SystemClose לכותרת. ב־iPad26/94 התקבל כל הרצף בחלון375pt, כולל תוצאה נראית לפני tap. [ראיה ו־attachments](qa/mobile-2026-11-08/ipad-window-94cdf7d.json). אין עדיין קבלת כל5 הסימולטורים.
- **IO-003 / QA-PRIVATE:** חמשת קובצי94 אומתו עצמאית: PNG/JSON/PDF146עמודים,1,526,437bytes וגיבוב Native תואם. userdebug/UID0/SELinux Enforcing בלי שינוי מוצר. ה־PDF אינו tagged; אין מדפסת פיזית. [ראיה](qa/mobile-2026-11-08/android-private-exports-94cdf7d.json).
- **PERF-003:** Android26 עם MemTotal1,548,780KB וליבה אחת עבר online/offline. ניסיון1GB נכשל בקדם משום שהאמולטור העלה אותו בפועל ל־1.5GB. אין טענת1GB, OOM או PSS של כלל Web. [ראיה](qa/mobile-2026-11-08/android-constrained-hardware.json).
- **SEARCH-005:** חמישה רצפי reflow, Android וחזרת iPad26 עברו. Web תיקון3 פורסם; [38 נכסי runtime זהים לפרסום](qa/mobile-2026-11-08/source-94cdf7d.json).

[PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11) מרכז את המועמד; docs/mobile-release-evidence-20261110 הוא checkpoint. מקור החוק ומועד2026-10-28 נשמרו. [BACKLOG](BACKLOG.md) ו־[EXTERNAL_ACTIONS](EXTERNAL_ACTIONS.md) מפרידים קבלה אוטומטית מפעולות חיצוניות.
