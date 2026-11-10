# מצב מימוש, אימות ופרסום

עודכן ב־10.11.2026. [קטלוג 63 הדרישות](docs/requirements.json) הוא מקור המצב המובנה; [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md) נגזר ממנו. מימוש, אימות ופרסום מסומנים בנפרד. אין להסיק קבלה מהימצאות קוד או מבדיקה ממתינה.

| ערוץ | מצב מאומת | פרסום בפועל |
|---|---|---|
| Web/PWA 1.3.9-dev, תיקון 3 | חמשת שערי Web של 06 עברו: 52 יחידות, 35 SHA/DOM, Node500, חמישה רצפי חיפוש, ארבעה רוחבים, 32 סריקות axe ומטמון offline | [reader](https://sargon17-green.github.io/consumer-law-reader/reader/), מקור cca785ed8b1f3d4c96bf25c0eb50e77b04899566, מטמון 453decfde812ec9b. פרסום 42778620385 הסתיים בהצלחה; 75 GET/SHA מאומתים, כולל alpha וה־APK |
| Android 1.3.9-dev/code17 | תיקוני מצב גדול ו־Ready עברו בניסוי רכיב 4819aa8: build ושלוש ריצות API26/31/36, online/offline. קבלה משולבת עדיין נדרשת | הציבורי נשאר 1.3.5-beta בחתימה המקורית. מועמד חדש הוא Debug/unsigned בלבד |
| iOS 1.3.9/build17 | ב־06 עברו iPhone26.2/18.5/16.0; iPad נכשל. תיקון scaling עבר בנפרד. תיקון חפיפת הכותרת עדיין בבדיקה | בניות סימולטור וארכיון מכשיר לא חתום בלבד; אין IPA חתום או TestFlight |

[ראיית פרסום Web](qa/mobile-2026-11-08/public-web-patch3-http-verification.json), [קבלת רכיב Android](qa/mobile-2026-11-08/android-state-cache-accepted.json), [קובצי Android שיוצאו ואומתו](qa/mobile-2026-11-08/android-private-exports-accepted.json).

## קבלה משולבת

הקבלה המלאה האחרונה שעברה היא 706a3bc: [Linux](qa/mobile-2026-11-08/acceptance-706a3bc-linux.json) ו־[iOS](qa/mobile-2026-11-08/acceptance-706a3bc-ios.json). היא אינה מכסה קוד מאוחר יותר.

המועמד 06e5533, שנבדק ב־merge checkout a7d6f42 בעל אותו tree, **נכשל בקבלה הכוללת**: ב־Android36 קרס תהליך הקורא ב־TransactionTooLargeException; בדיקת iPad נכשלה בהכנת החיפוש. הצלחות Web, API26/31 ושלושת iPhone נשמרות בהיקפן בלבד. [ראיה מלאה](qa/mobile-2026-11-08/acceptance-06e5533.json). אין למזג את 06 על סמך ההצלחות החלקיות.

## תיקוני ההמשך

- **DATA-003 / Issue14:** המצב האטום של Chromium נשמר ב־AtomicFile פרטי, וב־Bundle הפניית UUID+SHA קטנה. ב־4819aa8 נמדדו 1,615,960–1,617,964 בתים לפני הפיצול לעומת 1,036–1,060 בתים במצב Activity שאחרי הפיצול. יצירה מחדש, מלוא ההיסטוריה ו־Back/Forward עברו בשלושת האמולטורים. בדיקות נוספות לשיבוש digest, זהות התקנה וגבול 8MB נוספו לאחר הניסוי וטרם רצו ב־Native.
- **NATIVE-001:** המתנה מוגבלת ל־Ready אמיתי, עם generation לביטול callbacks ישנים. התאוששות לאחר עצירת renderer אמיתית ושימור סעיף/גופן/שאילתה עברו ב־API31/36. ב־API26 הפעולה הציבורית אינה קיימת ואינה מסומנת PASS.
- **IO-003 / QA-PRIVATE:** קובץ PDF אמיתי בן 146 עמודים נאסף ואומת מול גיבוב Native, לצד PNG/JSON תקינים. האיסוף מוגבל לאמולטור userdebug, UID0 ו־SELinux Enforcing; אין שינוי debuggable או הרשאות מוצר. ה־PDF אינו tagged; לא נבדקה מדפסת פיזית.
- **NATIVE-003 / Issue13:** orientations מפורשים תיקנו scaling של 44→30.9 נקודות. נוסף containerCornerOffset הרשמי של iOS26 לכותרת, עם fallback ל־16+. בניסוי 4c3596a נצפה חלון אמיתי ברוחב 375 נקודות וכפתורים 44×44, בהמשך0d3ef3f התפריט והשיתוף נפתחו במגע אמיתי. הריצה נכשלה בעת חזרה לחיפוש משום שהשיתוף לא נסגר;31b870a/run42815502889 דורש Close נצפה והיעלמות השיתוף. אין קבלה כוללת עדיין. [מצב מפורט](qa/mobile-2026-11-08/ipad-window-hit-test-progress.json).
- **SEARCH-005:** תיקון תוצאה נבחרת ו־offset לאחר שינוי פריסה עבר חמישה רצפי DOM נקיים ופורסם ב־Web תיקון 3. בדיקות Native נבחנות בנפרד; אין צורך בפרסום Web זהה נוסף בגלל תיקון Native בלבד.

[PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11) מרכז את המועמד. הענף docs/mobile-release-evidence-20261110 שומר checkpoint ותיעוד; ענפי הרכיבים אינם מסלול הפצה. לאחר קבלתם נדרשת רגרסיה מלאה על tree משולב אחד. המקור המשפטי ומועד אימותו 2026-10-28 נשמרו. [BACKLOG](BACKLOG.md) מפרט עבודה פתוחה; [EXTERNAL_ACTIONS](EXTERNAL_ACTIONS.md) כולל רק פעולות חיצוניות אמיתיות.


מקלדת Native: API26 עבר online/offline ב־5797c94. API31 עבר online; ב־offline שדה החיפוש היה מחוץ לתצוגה עקב שימור גלילת התוצאות. ה־fixture המשולב מגלגל אותו לתצוגה אחרי השחזור, ואז מחייב מגע והקלדה אמיתיים, IME נצפה, גבולות פיזיים ו־Back ששומר שאילתה. עדיין אין PASS משולב לשינוי הבדיקה.
