# כניסה לפרויקט והמשך עבודה

המאגר **Sargon17-Green/consumer-law-reader** הוא קורא חוק הגנת הצרכן, התשמ״א–1981: Android WebView, יישום SwiftUI עם WKWebView, וממשק Web/PWA משותף. אין לערבב עם פרויקט לוח השנה. מפרסמים ערוץ בשל מוקדם וממשיכים את הפיתוח; המידע במאגר ובקישורים להלן מספיק להמשך ללא שיחה.

## לקרוא תחילה

[מצב המימוש](IMPLEMENTATION_STATUS.md), [דרישות המוצר](PRODUCT_REQUIREMENTS.md) ו־[קטלוג 63 הדרישות](docs/requirements.json), [העבודה שנותרה](BACKLOG.md), [תקלות](KNOWN_ISSUES.md), [ארכיטקטורה](ARCHITECTURE.md), [בדיקות](TESTING.md), [הפצה](RELEASE_PROCESS.md), [החלטות](DECISIONS.md) ו־[פעולות חיצוניות](EXTERNAL_ACTIONS.md).

## מצב מאומת ופרסום

- **Web/PWA תיקון 3 פורסם:** [הקורא](https://sargon17-green.github.io/consumer-law-reader/reader/) ניתן להוספה למסך הבית. מקור `cca785ed8b1f3d4c96bf25c0eb50e77b04899566`, גרסת מטמון `453decfde812ec9b`. [פרסום 42778620385](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42778620385) הסתיים בהצלחה; כל 75 בדיקות HTTP/SHA256 עברו, כולל marker, האתר הקודם וה־APK. [ראיה קבועה](qa/mobile-2026-11-08/public-web-patch3-http-verification.json).
- **Android הציבורי נשאר 1.3.5-beta**, ב־[קישור הקבוע](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk). אין מפתח חתימה מקורי נגיש. מועמדי 1.3.9-dev/build17 הם Debug או unsigned; אין להציגם כשדרוג חתום.
- **iOS 1.3.9/build17 לא הופץ:** קיימות בניות סימולטור וארכיון מכשיר לא חתום. אין IPA חתום או TestFlight.
- הקבלה המלאה האחרונה שעברה היא `706a3bc`: [Linux 42764913617](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42764913617) ו־[iOS 42764913616](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42764913616). היא אינה מכסה תיקונים חדשים.
- המועמד `06e5533` עבר את חמשת שערי Web, Android 26/31 ושלושת סימולטורי iPhone, אך **נכשל בקבלה הכוללת** ב־Android 36 ובבדיקת iPad. [סיכום מדויק](qa/mobile-2026-11-08/acceptance-06e5533.json). אין למזגו על סמך הצלחות חלקיות.

## ענפים והצעד הבא

יש לרענן קודם את ראשי הענפים והריצות ב־GitHub; אין להניח ש־hash ישן הוא האחרון.

1. [PR 11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11), בענף `fix/pastafari-date-android-20261028`, מרכז את העבודה. בסיס main המקורי הוא `016b3de352dabe97f51b34b78ff803965b6cd40d`. הענף `docs/mobile-release-evidence-20261110` מחזיק גם checkpoint של תיקוני ההמשך וראיותיהם. ממשיכים מהגרסה המעודכנת המתועדת ב־PR, בלי לדרוס ענפים מקבילים.
2. **P0 / DATA-003 / [Issue 14](https://github.com/Sargon17-Green/consumer-law-reader/issues/14):** ב־06/API36 מצב Chromium בגודל 1,204,232 בתים גרם ל־TransactionTooLargeException. זה כשל בתהליך היישום, שונה מתקלה היסטורית ב־MediaProvider. התיקון בענף `work/android-state-cache-20261110`, החל מ־`6ed474ff959f103b69fe3c8746f97a5cda445309`, שומר מצב אטום ב־AtomicFile פרטי ונותן ל־Bundle רק UUID וגיבוב. נדרשות שלוש בדיקות Android מלאות, מצב אמיתי מעל 1MB, Bundle קטן מ־50KB, יצירה מחדש ו־Back/Forward תקינים. [ראיית הכשל](qa/mobile-2026-11-08/android-binder-state-before.json).
3. **iPad / [Issue 13](https://github.com/Sargon17-Green/consumer-law-reader/issues/13):** הצהרת orientations תיקנה scaling, אך לחיצה אמיתית חשפה חפיפה של פקדי המערכת לכפתור הפעולות. בענף `work/ipad-header-hit-20261110` נוספה התאמה באמצעות `containerCornerOffset` הרשמי של iOS 26, עם fallback לגרסאות קודמות. ניסוי `316f399` נכשל בהכנת הבדיקה משום ש־XCTest מחזיר placeholder בתור value; אינו פסק דין על תיקון הכותרת. ההמשך `2686655362862e91ab6fbf3f6c140ff4e309bd2f` מתקן זאת ושומר בדיקות לחיצה אמיתיות על תפריט ושיתוף לאחר שינוי חלון. [ראיית החפיפה](qa/mobile-2026-11-08/ipad-header-occlusion-before.json).
4. לאחר קבלת התיקונים: להעביר רק קוד מוצר ובדיקות קבועות ל־PR 11, להריץ רגרסיה משולבת על ראש ידוע, ולעדכן קטלוג וראיות. אין להעביר workflows אבחון או דגלי `printOnly`/`rendererOnly`. להסיר draft ולמזג רק לאחר completed PASS לכל השערים המהותיים ובהתאם להגנות המאגר.
5. Web תיקון 3 כבר מכיל את SEARCH-005. אין להפיצו שוב רק בגלל שינוי Android או Swift. הפצות נוספות דורשות ערך חדש, התאמת נכסי runtime למקור שנבדק, שימור alpha/APK ו־HTTP של הפרסום בפועל.

## חוזים ומגבלות

המקור המשפטי חייב להישאר SHA256 `de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9`; תאריך האימות **2026-10-28**. `verify_release.py` חייב להעביר 35 בדיקות SHA/DOM/IDs/קישורים ומשאבים. אין שינוי משפטי, עדכון תאריך, פרשנות חדשה, ענן, Analytics או פרסומות.

מצב Chromium ב־cache הוא זמני ומותנה באותה התקנת OS/app/provider. הוא אינו גיבוי נייד. פגיעה במטמון מחזירה למיקום הקריאה הלוגי; הגדרות, נושאים וקישורים נשמרים בנפרד. איסוף ראיות Android מורשה רק באמולטור userdebug, עם SELinux Enforcing ובלי שינוי debuggable של המוצר. קובצי PNG/JSON/PDF וגיבוב PDF נבדקים בפועל; פלט שגיאת ADB אינו ראיה תקינה.

תיקונים רגילים, בדיקות, PR, מיזוג ופרסום שעברו שעריהם מותרים אוטונומית. pending אינו חסם או PASS. אין force-push, החלפת זהות חתימה או הצגת Debug/סימולטור כהפצה מקורית. מפתח חתימה, Apple Team/ASC, אישור תנאים או זכויות ומכשיר פיזי שאינו זמין הם פעולות חיצוניות בלבד; ההוראות ב־EXTERNAL_ACTIONS. אין צורך בהרצה במחשב המשתמש.
