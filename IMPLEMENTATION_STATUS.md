# מצב מימוש, אימות ופרסום

עודכן ב־11.11.2026. [63הדרישות](PRODUCT_REQUIREMENTS.md) נגזרות מ־[הקטלוג](docs/requirements.json). מימוש, אימות ופרסום נבדלים. queued/in_progress אינםPASS או חסם.

| ערוץ | מה אומת | מה פורסם |
|---|---|---|
| Web/PWA1.3.9-dev תיקון3 |52יחידות,35SHA/DOM,500UTF16,5רצפי reflow,4רוחבים/32axe ומטמון offline; [75HTTP/SHA חיים](qa/mobile-2026-11-08/public-web-readonly-recheck.json) |[reader](https://sargon17-green.github.io/consumer-law-reader/reader/), מקורcca785e, הוספה למסך הבית |
| Android1.3.9-dev/code17 |94 עבר9Linux/Android ו־26/31/36online/offline כולל PDF146עמודים ו־cache עוין;6d העביר תיקון IME ב־31;1.5GB/ליבה אחת עבר בנפרד |הציבורי נשאר1.3.5-beta במפתח המקורי. החדש Debug/unsignedAPK/AAB בלבד |
| iOS1.3.9/build17 |חלוןiPad94, שיתוף4bc ו־PDFמלאb916 עברו בהיקפם;200 העביר Ready/8טעינות ב־18.5 ו־c853 העביר UI/print-preview/Close מלא ב־iPad26.2 |סימולטורים וארכיון מכשיר לא חתום; אין IPA חתום או TestFlight |

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
