# מצב מימוש, אימות ופרסום

## עדכון נוכחי — 16.11.2026: קבלה, מיזוג ופרסום ה־Web

**מימוש קיים ב־main:** [PR #24](https://github.com/Sargon17-Green/consumer-law-reader/pull/24) מוזג ב־`ae494547ba998a94070293d9914530144d6cf0bb`, אחרי **15/15 completed/success** ב־SHA `5b0e537420a1c9eb968a5d1a66af00f17d27f7c3`. מניפסט העדכונים פורסם קודם לכן ב־PR #28, ונבדק עם HTTP 200 וגיבוב SHA-256. מכניקת העדכונים היא *קריאת מידע בלבד* בעת פתיחה/חזרה לאפליקציה, עם הודעה כאשר יש מהדורת חוק מאושרת גבוהה יותר; היא אינה משנה את נוסח החוק המותקן.

**Web/PWA:** [פריסת Actions #43774661018](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43774661018) הסתיימה בהצלחה. אומתו 76 קבצים באתר החי ו־36 קבצים מחוץ ל־`reader/` נשמרו; בדיקת PWA לא־מקוונת עברה. זו **הפצת Web מעודכנת**, לא שדרוג Native.

**Android:** חבילת QA מבודדת נבדקה במכשיר פיזי, כולל HTTP 200 ואזהרה מדומה; החבילה הוסרה והאפליקציה הציבורית לא שונתה. ה־APK החתום האחרון לציבור נשאר **v1.3.5-beta**. קוד 1.3.9-dev עדיין אינו Release חתום; אין לפרסם Debug כעדכון.

**iOS:** בדיקות המועמד ב־PR #24 עברו 6/6 בפעם המאוחרת ביותר, אך הרצות קודמות נכשלו ב־Files/ShareSheet; מעבר אחד אינו מוכיח יציבות. אין IPA חתום או TestFlight. ענפי QA #30/#31 עדיין נבדקים, ו־#32 אינו תיקון שאושר (13/15). תוצאות push CI אחרי מיזוג נבחנות בנפרד מתוצאות PR. יתר הסעיפים במסמך זה הם היסטוריים.



עודכן ב־11.11.2026. [63הדרישות](PRODUCT_REQUIREMENTS.md) נגזרות מ־[הקטלוג](docs/requirements.json). מימוש, אימות ופרסום נבדלים. queued/in_progress אינםPASS או חסם.

| ערוץ | מה אומת | מה פורסם |
|---|---|---|
| Web/PWA1.3.9-dev תיקון3 |52יחידות,35SHA/DOM,500UTF16,5רצפי reflow,4רוחבים/32axe ומטמון offline; [75HTTP/SHA חיים](qa/mobile-2026-11-08/public-web-readonly-recheck.json) |[reader](https://sargon17-green.github.io/consumer-law-reader/reader/), מקורcca785e, הוספה למסך הבית |
| Android1.3.9-dev/code17 |94 עבר9Linux/Android ו־26/31/36online/offline כולל PDF146עמודים ו־cache עוין;6d העביר תיקון IME ב־31;1.5GB/ליבה אחת עבר בנפרד |הציבורי נשאר1.3.5-beta במפתח המקורי. החדש Debug/unsignedAPK/AAB בלבד |
| iOS1.3.9/build17 |חלוןiPad94, שיתוף4bc ו־PDFמלאb916 עברו בהיקפם;200 העביר Ready/8טעינות ב־18.5 ו־c853 העביר UI/print-preview/Close מלא ב־iPad26.2 |סימולטורים וארכיון מכשיר לא חתום; אין IPA חתום או TestFlight |

## תוצאות הקבלה המאוחדת — הושלמו ב־11.11.2026

[דו"ח הלוגים המלא](qa/mobile-2026-11-11/completed-acceptance-triage-20261111.md) מבדיל בין ביצוע קודם לבין האישור החסר: source/browser/Android **9/9 jobs PASS** ב־[42967750924](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750924), iOS **3/6 jobs PASS ו־3 FAIL** ב־[42967750794](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750794), שניהם על `5792b66`. ה־iOS FAIL הוא במבחני UI של print-preview ב־XXXL, ביטול שחזור ב־iPhone18.5 וסגירת שיתוף ב־iPad18.5. אין לאשר PR11. בנוסף, ניסוי Files נפרד [42968670868](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42968670868) עבר **Save אמיתי** ל־PDF חדש ב־LocalStorage על iPhone26.2; קובץ בן 136 עמודים, 1,302,508 בתים. אין להכליל זאת ל־iOS כולו.

## המועמד המאוחד

[027](qa/mobile-2026-11-08/candidate-027-followup.json) הסתייםLinux8/9PASS ו־iOS4/6PASS, כולל XXXL בפועל. כשלים: Android36offlineIME, iPad26PrintClose ו־iPhone18.5lifecycle. הוא אינו מועמד מאושר למיזוג. [תמונות כשל מקוריות](qa/mobile-2026-11-08/screens/README.md) נשמרו ב־Git.

[תיקוני ההמשך](qa/mobile-2026-11-11/components-accepted.json) עברו במבחנים ממוקדים: Android31online/offline6d; lifecycle ו־8טעינות חדשות iOS18.5/200; רצף iPad26.2 מלא348.896s עם page-preview ו־Close ב־c853. generation guard מונע callback ישן לעדכן Ready בזמן ניווט חדש; אין טענה שזו הסיבה היחידה לכשל027. בדיקת IME ממשיכה לדרוש הקלדה Native, חלון מערכת, שדה גלוי ו־Back משמר חיפוש.

[PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11) מרכז את המועמד החדש. קבלה נדרשת על tree אחד: **9Linux/Android+6iOS**. iOS מריץ9מבחני WK/policy בכל פרופיל ואת בדיקות ה־UI המתאימות; אין only-testing של אבחון. Xcode מקמפל app+tests לפני boot. תקציב תרחיש ה־UI המורחב הוא480s בעקבות מדידה348.896s, כשכל תנאי מגע/מקלדת/preview/סגירה נשמר. אין למזג לפני completed PASS ובדיקת הגנות.

## מגבלות ופעולות פתוחות

- שמירת PDF ב־iOS דרך Save-to-Files ומדפסת פיזית נפרדות מ־formatter. ניסוי Files מתקדם בענף נפרד; סרגל Options לבדו אינו הוכחת שמירה. קבלה דורשת Save ממשי ו־PDF חדש מקומי עם hash, כל העמודים ו־ink ראשון/אמצע/סוף.
- כל38נכסי runtimeWeb זהים לפרסום; אין שחרור Web חדש רק בשל Native. מקור החוק והתאריך2026-10-28 נשמרים.
- PSS/CPU94 הם של תהליך היישום עם instrumentation; indexMilliseconds אחרי חיפוש הוא גישה ממוטמנת. אין טענת אינדקס קר0ms או כלל תהליכיWeb. [מדידות](qa/mobile-2026-11-08/android-performance-94cdf7d.json).
- [Issue12](https://github.com/Sargon17-Green/consumer-law-reader/issues/12) נסגר לפי PDFAndroid.13/14/15/16 פתוחים לקבלה משולבת ומיזוג;7 לחתימה ושדרוג תואמים.
- [BACKLOG](BACKLOG.md), [תקלות](KNOWN_ISSUES.md) ו־[פעולות חיצוניות](EXTERNAL_ACTIONS.md) מפרטים את ההמשך. אין כיסוי פיזי, אישור חנות או TestFlight.
