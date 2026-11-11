# קבלה מאוחדת — ממצאי ריצות שהושלמו ב־11.11.2026

מועד הבדיקה: 11.11.2026. מסמך זה מבוסס על **ריצות completed ועל לוגים** ואינו מכריז על מוכנות לפרסום. אין להשתמש בשיחה קודמת כמקור אמת. אין שינוי ב־HTML המשפטי או בגרסאות ההפצה.

## מקור המועמד

- PR: [#11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11), טיוטה פתוחה בעת הבדיקה.
- ראש המועמד שנבדק: `5792b66bc0255c9cf110f1b4af908dd9e25ed620`; קומיט הבסיס ב־main: `016b3de352dabe97f51b34b78ff803965b6cd40d`.
- [Linux, Web and Android run 42967750924](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750924): `completed/success`, **9/9 jobs success** — source/browser, ארבעה רוחבי דפדפן, בניית Android debug ואמולטורים API26/31/36. APK/AAB של מועמד זה אינם חתומים בתעודת השדרוג המקורית.
- [Native iOS run 42967750794](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750794): `completed/failure`, **3/6 jobs success**. כל שש העבודות עברו בניית app+tests. מבחני UI נכשלו בשלושה פרופילים; אין `PASS` מאוחד.

## פירוט iOS מאוחד — ששת הפרופילים

| פרופיל | תוצאה | הראיה העיקרית |
|---|---|---|
| iPhone iOS 26.2 | PASS | עבודת הסימולטור כולה הצליחה |
| iPhone iOS 26.2 accessibility XXXL | FAIL | `ReaderUITests.swift:101`: לא נמצא תא נגישות `Page 1 of ` בתוך 45 שניות בחלון ההדפסה של iOS 26 |
| iPad iOS 18.5 | FAIL | `ReaderUITests.swift:132`: שאילתת AX לאיתור Close ב־ActivityListView נקטעה (`Interrupted by waiter`) |
| iPad iOS 26.2 | PASS | עבודת הסימולטור כולה הצליחה |
| iPhone iOS 16.0, בדיקת זמינות runtime | PASS | העבודה הסתיימה בהצלחה; להיזהר מהסקת כיסוי runtime 16 אם נבדקה רק זמינות ולא הורץ runtime זה בפועל |
| iPhone iOS 18.5 | FAIL | `ReaderUITests.swift:119`: כפתור Cancel/Close/ביטול בחלון שחזור מקובץ לא הופיע תוך 60 שניות; תצלום עץ ה־AX מראה את ממשק היישום, ואין ראיה מספקת שסייר הקבצים נפתח |

לכל שלושת הכשלים הפניה ללוגי jobs תחת [run 42967750794](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750794). אין לקבוע מתוך הלוג בלבד אם הכשל במוצר, באוטומציית XCTest, ב־UIKit או באינטראקציית תזמון. שגיאות מערכת מסוג `RBSAssertionErrorDomain` ליד מבחני WKWebView שעברו אינן לבדן סיבת כשל.

## ראיה עצמאית חדשה: שמירת PDF ב־iOS Files

[run 42968670868](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42968670868), בענף `work/ios-files-cell-save-20261110`, ראש `9c541b8882109e59d371f2ba32603048fd532afa`, הסתיימה `completed/success`.

לוג הבדיקה מציג `SYSTEM_PDF_SAVE_UI`: לחיצה בפועל על Save של מערכת iOS, סגירת מסך השירות וחזרה לממשק הקורא. בדיקת המארח מצאה PDF **חדש** תחת `group.com.apple.FileProvider.LocalStorage`:
- גודל: **1,302,508 בתים**.
- SHA-256: `1a4c70956027e8806bee3bb201be1b8481bd5e1240912d56d913245e65a55182`.
- **136 עמודים**; תוצאת `PASS` לאימות ספירת עמודים ורסטר ink בעמודים 1, 69, 136.
- היקף הראיה: שמירה למערכת Files בסימולטור iPhone iOS 26.2, לא שמירה בכל פרופיל, הדפסה פיזית או ביקורת PDF נגיש/מתויג. בדיקה זו אינה ב־SHA המועמד המאוחד, ולכן לא הופכת אותו ל־PASS.

יש להבחין בין מסמך PDF זה ובין בדיקת formatter נפרדת שהניבה 126 עמודים בתרחיש קודם: אין להתייחס להפרש ככשל בלי להשוות קלטים, גרסאות, מסלולי ההפקה והגדרות הדפסה.

## סדר המשך מדויק

1. לאסוף את צילומי המסך, היררכיית AX ותוצרי ה־xcresult של שלוש עבודות iOS שנכשלו. לאתר האם חלון המערכת הוצג, אילו פקדים היו נגישים ומהם השלבים שנכשלו. להשוות לריצות ממוקדות `200d5b7`, `c853d3b`, `4bc...` שעברו, בלי לייחס סיבת שורש לפני אימות.
2. לתקן את ההתנהגות או את איתור רכיבי המערכת באופן המותנה בגרסת iOS; **לא** להסיר את דרישות keyboard native, עמוד PDF ממשי, Save, סגירה אמיתית, בדיקת שיתוף או שחזור.
3. להריץ מחדש את **אותה מטריצת קבלה — 9 Linux/Android + 6 iOS על אותו head/tree**. אין לפצל PASS בין commits ואין להחשיב queued/in_progress כהצלחה או כחסימה.
4. רק לאחר completed PASS מאוחד ולפי הגנות הענף, לשקול הסרת draft ומיזוג PR #11. עם המיזוג לבצע אימות Pages וספקי הקישור הקבוע בלי להחליף חתימה. Issues 13/14/15/16 ייסגרו רק לאחר תנאיהם.
5. Android הציבורי נותר **1.3.5-beta**, ו־Web/PWA כבר זמין. ללא מפתח Android המקורי וללא Apple Team/ASC אין לשחרר APK שדרוג או IPA/TestFlight חתומים. ראו `EXTERNAL_ACTIONS.md`.

## עקרון שקיפות

תוצאות 9/9 ו־3/6 נכונות לקומיט `5792b66` שנבדק, ולא בהכרח לראש ענף מאוחר יותר. הוספת מסמך זה משנה את SHA הענף אך לא את נכסי runtime; יש לשמור את ההבחנה במפורש. כל הניתוח כאן נשען על ממצאים, והפרשנות למקור הכשלים נשארת פתוחה.
