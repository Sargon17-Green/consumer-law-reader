# היסטוריית פרסום וערוצים

| ערוץ / גרסה | סטטוס | מקור וראיה | התקנה |
|---|---|---|---|
| Android v1.3.5-beta | הפצה ציבורית קיימת, ללא החלפה במחזור זה | [Release](https://github.com/Sargon17-Green/consumer-law-reader/releases/tag/v1.3.5-beta); APK SHA2562772e3d8195de2d9a66edc8cdbc9e0940ac71f8cb55f1597dcc7c122120101af; חתימת ההפצה המקורית | [latest.apk קבוע](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk) |
| Web1.3.9-dev — בטא ביניים | **פורסם ב־10.11.2026**;74 בדיקות SHA256/HTTP עברו, כולל האתר הקודם וה־APK | commit83fe5ec4a0d17c209088354c4ff748f63d7188a0; [run42718069159](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42718069159) build הצליח, deploy נדחה ב־environment; אין PASS כולל לריצה. [אימות האתר החי](qa/mobile-2026-11-08/public-web-http-verification.json) מוכיח פרסום רגיל מ־gh-pages בלי שינוי ההגנה | [ממשק הקריאה](https://sargon17-green.github.io/consumer-law-reader/reader/), הוספה למסך הבית ב־Safari/Chrome |
| Android1.3.9-dev/code17 | מועמד קוד/Debug/unsigned APK/AAB; **לא הפצה ציבורית חתומה** | PR11 ו־IMPLEMENTATION_STATUS | אין קישור שדרוג ציבורי חדש |
| iOS1.3.9/build17 | סימולטור ו־archive לא חתום; **לא TestFlight/IPA** | iOS42683016332 הצליח בכל ארבע הסביבות | אין התקנה Native ציבורית לאייפון |

Web בטא מוסיף ביחס לממשק הקריאה המוקדם: חיפוש ומיפוי עברי מדויקים, גיבוי נייד עם preview/rollback, קישורים ושימור מצב, CSP/גבולות משאבים, נגישות ותיקון רוחב לכל66 התקנות וגופן גדול. זו גרסת Web/PWA; אין הצגת התקנתה כיישום SwiftUI. רשומת הפצה אינה מאשרת דיוק משפטי, חתימה או בדיקה פיזית.
