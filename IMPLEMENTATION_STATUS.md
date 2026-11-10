# מצב מימוש, אימות ופרסום

עודכן ב־10.11.2026. [63 הדרישות](PRODUCT_REQUIREMENTS.md) נגזרות מ־[קטלוג המצב](docs/requirements.json). מימוש, אימות ופרסום נבדלים; pending אינו PASS או חסם.

| ערוץ | מה אומת | מה פורסם |
|---|---|---|
| Web/PWA1.3.9-dev, תיקון3 |52 יחידות,35 SHA/DOM,Node500,5 רצפי reflow,4 רוחבים,32 סריקות axe ומטמון offline. [75 HTTP/SHA עברו שוב ב־16:55UTC](qa/mobile-2026-11-08/public-web-readonly-recheck.json) |[reader](https://sargon17-green.github.io/consumer-law-reader/reader/), מקור cca785e ומטמון453decfde812ec9b. ניתן להוספה למסך הבית |
| Android1.3.9-dev/code17 |94 עבר את כל9 Linux/Android, API26/31/36 online/offline, IME אמיתי, cache עוין, שדרוג בזהות QA, SAF ושיתוף; PDF146עמודים אומת עצמאית. תצורת1.5GB/ליבה אחת עברה בנפרד |הציבורי נשאר1.3.5-beta במפתח המקורי; מועמד חדש Debug/unsigned בלבד |
| iOS1.3.9/build17 |iPad26/94 עבר חלון מערכת375pt/פקדים44pt וכל רצף התפריט/שיתוף/חזרה.4bc עבר iPhone16/iPad18.5 עם Close ממשי ושחזור חיפוש. PDF מלא126עמודים עבר ב־b916 ואומת ב־Poppler |סימולטורים וארכיון מכשיר לא חתום; אין IPA חתום או TestFlight |

## מצב הרגרסיה027 — אין אישור למיזוג

[ראיות ומעקב](qa/mobile-2026-11-08/candidate-027-followup.json): ריצה42861539480 הסתיימה8/9Linux/Android PASS, אך API36 offline נכשל לפני הקלדה במקלדת. ב־42861539523 עברו iPhone26.2/16 ו־iPad18.5; iPad26.2 נכשל בסגירת Print למרות מגע במרכז Close, ו־iPhone18.5 נכשל ב־ReferenceError במהלך בדיקת lifecycle. בדיקות ה־UI שלו עברו. פרופיל XXXL עדיין רץ בזמן התיעוד. אין הסקת PASS מהמתנה.

ניסוי Android850 העביר26 אך חשף איתור editable בחלון IME ב־31. התיקון הבא bfcb7e1 מאתר חלון יישום וממשיך לדרוש IME אמיתי, שדה גלוי, קלט Native ו־Back משמר חיפוש. ניסויי iOS f522c22 ו־278d13e עוקבים בנפרד אחרי lifecycle וסגירת Print/שמירה דרך Files; אין להעביר traces או only-testing למועמד. כל ניסוי נשמר ב־GitHub.

## קבלה משולבת נדרשת

[94cdf7d](qa/mobile-2026-11-08/acceptance-94cdf7d.json) הסתיים9 Linux PASS ושלושה מחמישה iOS PASS; שני מבחני שיתוף ישנים נכשלו. הוא אינו מועמד מאושר למיזוג. תיקון ההמשך מחבר UIKit completion למצב SwiftUI לפי UUID, ממתין ל־Close hittable ואינו משתמש ב־swipe כתחליף לסגירה.

[4bc / ריצה42854077139](qa/mobile-2026-11-08/ios-legacy-share-component-accepted.json) העביר iPhone16 ו־iPad18.5: ביטול שיתוף, היעלמות ActivityListView, סיבוב, הפעלה מהסמל ושאילתה14. callback ישן אינו סוגר שיתוף חדש. [b916 / ריצה42856626665](qa/mobile-2026-11-08/ios-complete-pdf-component.json) הפיק את כל126 עמודי UIKit; Ubuntu/Poppler בדק independently את ה־ZIP, PDF, מניין העמודים וטקסט בתחילה/אמצע/סוף. זו אינה שמירה בממשק Files או מדפסת פיזית.

[PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11) מרכז כעת את הקוד, התיעוד והבדיקות הקבועות. ראש המועמד נקבע מ־GitHub ולא מ־hash עצמי בתוך קובץ. השער הסופי הוא **9 Linux/Android ו־6 מקרי סימולטור iOS** על tree אחד: שלושת iPhone26.2/18.5/16, שני iPad26.2/18.5 ועוד iPhone26.2 בגודל נגישות XXXL. הבדיקות החדשות דורשות גם מקלדת תוכנה אמיתית ושדה חיפוש מעליה. אין קבלה שלהן עד completed PASS. ניסוי הגודל הממוקד0c9507a/run42858470735 נבחן בנפרד; queued אינו חסם.

## ראיות ומגבלות

- [Android94](qa/mobile-2026-11-08/acceptance-94cdf7d.json): raw Chromium1,615,960–1,617,964bytes מול Activity1,036–1,200bytes; recreate/history/Back/Forward ושיבוש hash/התקנה/8MB עברו. [קובצי הייצוא](qa/mobile-2026-11-08/android-private-exports-94cdf7d.json).
- [iPad26/94](qa/mobile-2026-11-08/ipad-window-94cdf7d.json): שינוי חלון1032→375pt, תפריט ושיתוף במגע ממשי, סגירה ותוצאה נראית לפני tap. אין לייחס ל־CSS בלבד.
- [חומרה מצומצמת](qa/mobile-2026-11-08/android-constrained-hardware.json): MemTotal1548780KB וליבה אחת, online/offline. ניסיון1GB נדחה כשהאמולטור כפה1.5GB; אין טענת OOM.
- [מדידות Native94](qa/mobile-2026-11-08/android-performance-94cdf7d.json): PSS/CPU של תהליך היישום עם instrumentation בלבד; indexMilliseconds אחרי חיפוש הוא cached access. אין להסיק ממנו זמן אינדקס קר.
- כל38 נכסי Web של94 זהים לפרסום. אין שחרור Web חדש בגלל שינוי Native בלבד. מקור החוק ומועד2026-10-28 נשמרו.
- [Issue12](https://github.com/Sargon17-Green/consumer-law-reader/issues/12) נסגר לפי קבלת PDF ב־Android. Issues13/14/15 נשארים עד קבלה משולבת ומיזוג; Issue7 עד חתימה/שדרוג/פרסום תואמים.

הקבלה המלאה ההיסטורית706a3bc נשמרת בהיקפה; היא אינה מכסה תיקונים חדשים. מגבלות ופעולות המשך ב־[BACKLOG](BACKLOG.md), [KNOWN_ISSUES](KNOWN_ISSUES.md), [EXTERNAL_ACTIONS](EXTERNAL_ACTIONS.md).
