# היסטוריית פרסום וערוצים

| ערוץ / גרסה | סטטוס | מקור וראיה | התקנה |
|---|---|---|---|
| Android v1.3.5-beta | הפצה ציבורית קיימת, ללא החלפה במחזור זה | [Release](https://github.com/Sargon17-Green/consumer-law-reader/releases/tag/v1.3.5-beta); APK SHA2562772e3d8195de2d9a66edc8cdbc9e0940ac71f8cb55f1597dcc7c122120101af; חתימת ההפצה המקורית | [latest.apk קבוע](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk) |
| Web1.3.9-dev — בטא ביניים | **פורסם ב־10.11.2026**;74 בדיקות SHA256/HTTP עברו, כולל האתר הקודם וה־APK | commit83fe5ec4a0d17c209088354c4ff748f63d7188a0; [run42718069159](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42718069159) build הצליח, deploy נדחה ב־environment; אין PASS כולל לריצה. [אימות האתר החי](qa/mobile-2026-11-08/public-web-http-verification.json) מוכיח פרסום רגיל מ־gh-pages בלי שינוי ההגנה | [ממשק הקריאה](https://sargon17-green.github.io/consumer-law-reader/reader/), הוספה למסך הבית ב־Safari/Chrome |
| Android1.3.9-dev/code17 | מועמד קוד/Debug/unsigned APK/AAB; **לא הפצה ציבורית חתומה** | PR11 ו־IMPLEMENTATION_STATUS | אין קישור שדרוג ציבורי חדש |
| iOS1.3.9/build17 | סימולטור ו־archive לא חתום; **לא TestFlight/IPA** | iOS42683016332 הצליח בכל ארבע הסביבות | אין התקנה Native ציבורית לאייפון |

Web בטא מוסיף ביחס לממשק הקריאה המוקדם: חיפוש ומיפוי עברי מדויקים, גיבוי נייד עם preview/rollback, קישורים ושימור מצב, CSP/גבולות משאבים, נגישות ותיקון רוחב לכל66 התקנות וגופן גדול. זו גרסת Web/PWA; אין הצגת התקנתה כיישום SwiftUI. רשומת הפצה אינה מאשרת דיוק משפטי, חתימה או בדיקה פיזית.


## Web1.3.9-dev — תיקון2,10.11.2026

**פורסם בפועל** מתוך commitc3e9d9e5a62454b2d6e857476aae284c093cefef; cache721a4e865027bc53. סטטוס offline מבוסס כל38 נכסי החובה ומוצג בלוח ההתקנה; יעד בחקיקת משנה מגיע מתחת לכפתור החזרה לאחר focus. [פרסום42765882923](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42765882923) ו־[Pages42766006491](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42766006491) הצליחו; gh-pagesdcd37048893b5747a9f794dd0632e7d4534c8c28. [כל75GET/SHA256](qa/mobile-2026-11-08/public-web-patch-http-verification.json) עברו,36 קבצים קיימים נשמרו וה־APK הציבורי נשאר זהה. runtime תואם38נכסים של706a3bc שנבדק בארבעה רוחבים/32axe; build הפרסום עצמו עבר47unit/PWA ושלמות. עדכון מותקן עשוי להופיע בפתיחה הבאה לאחר השלמת עדכון המטמון. זו עדיין בטא Web; לא גרסה Native חתומה חדשה.

## Web תיקון3 —10.11.2026, פורסם

Sourcecca785ed8b1f3d4c96bf25c0eb50e77b04899566; runtime453decfde812ec9b. שימור תוצאה נבחרת לאחרreflow/שינוי גובה, ללא שינוי משפטי. source52unit,35SHA/DOM,Node500,5search sequences,4widths/32axe ו־PWAoffline עברו. [run42778620385](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42778620385) completedsuccess וכל75HTTP/SHA עברו. [HTTP](qa/mobile-2026-11-08/public-web-patch3-http-verification.json); alpha וה־APK הציבורי נשמרו. Native06נכשל בבדיקותמשלימות; אין לייחסלו releaseחדש.
