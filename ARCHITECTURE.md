# ארכיטקטורת קורא חוק הגנת הצרכן

הפרויקט הוא קורא חוק בעברית ל־Android, ל־iPhone/iPad ול־Web/PWA. אין בו חשבונות, backend של נתוני משתמש או telemetry. הוא אינו פרסום ממשלתי. דיוק משפטי אינו חלק ממחזור ההנדסה.

| שכבה | מיקום ותפקיד | חוזה |
|---|---|---|
| מקור | `original/`, `metadata/editorial_status.json`, `NOTICE_HE.md` | מקור החקיקה והערות נשמרים בדיוק; אין קידום תאריך בדיקה |
| יצירת חבילה | `scripts/build_web.py`, `bundled_assets.py`, `prepare_typed_sources.py` | dist נקי; CSP hash; קבצים מקומיים ו־manifest/SW; sourceCommit/tree/dirty בראיות |
| חיפוש ונתונים | `web/mobile-core.js` | נרמול עברי ומיפוי UTF-16; schema2, אימות, limits, journal/rollback/recovery |
| ממשק | `mobile.js`, `mobile.css`, `mobile-shell.html` | ניווט/היסטוריה/סעיף נראה/חיפוש; פירוק טבלאות פרוזה לתצוגה בלבד, אזורי גלילה מקומיים לטבלאות נתונים |
| נושאים/מקורות | `mobile-topics.js`, `mobile-sources.js`, `typed-sources/` | נושאים וקישורים מקומיים; תיבות מקורות ללא שינוי תוכן או המצאת שיוך |
| Android | `MainActivity.java`, `AttachmentProvider.java`, manifest/res | HTTPS law.local מתוך assets; גשר למסמך מקומי; SAF, Clipboard, Sharesheet, Print; Java8 ללא Gradle dependency stack |
| iOS | SwiftUI `ConsumerLawReaderApp.swift`, `ReaderPolicy.swift`, `ios/project.yml` | WKWebView/file מוגבל ל־dist; weak/main-frame message guard; Files, UIKit Print/Share, Dynamic Type |
| Web | `manifest.webmanifest` ו־`sw.js` נוצרים ב־build | HTTPS/standalone/סמל קבוע, מטמון מקומי; פינוי מטמון מערכת אינו בשליטת האפליקציה |
| CI | `.github/workflows/ci.yml`, `ios-ci.yml` | Python/Node/DOM/axe, APK/AAB, אמולטורים וסימולטורים אמיתיים; ראיות ותוצרי כשל |
| פרסום | `deploy_web.yml`, `prepare_reader_site.py`, `verify_public_reader.py` | רק reader/ משתנה בענף gh-pages; אתר alpha ו־APK נשמרים |

גבולות אמון: טקסט המקור הארוז אמין; קלט משתמש/קובץ גיבוי/URL/מידע רשת אינם אמינים. אין WebView כללי לאתרים חיצוניים. רק שלושה נתיבי JSON מוגדרים מותרים לנתוני תאריך; אין script/frame חיצוני. קישור חיצוני או שיתוף נפתחים רק בפעולת משתמש.

אחסון: העדפות ונושאים ב־localStorage באותו origin; היסטוריית מיקום/חיפוש נפרדת. גיבוי הוא UTF-8 JSON, whitelist של תשעה מפתחות, 1MB; אין ענן אוטומטי. Android אינו שם גיבוי גדול ב־Bundle: נעשה שימוש ב־AtomicFile פרטי. פרטי schema ומקרי קצה: [פורמט הגיבוי](docs/SETTINGS_BACKUP_FORMAT_HE.md).

חוזי ממשק: `lawMobile` חושף ניווט/חיפוש/שמירת session; `lawSettings` חושף exportJSON/prepareImport/applyImport; `NativeLaw` קיים רק במעטפת המקורית ומעביר פעולות מערכת. Native מאשר העתקה בפועל; קלט גדול נשמר שלם ב־fallback נגיש. אין להוסיף HTML מתוך קלט או להעביר טקסט חוק דרך רשת.

ב־Android code17/min26/target36; iOS build17/min16/families1,2. אין בינארי Native תלוי CPU של הפרויקט; DEX רץ ב־ABIs הרלוונטיים. CI משתמש ב־x86/x86_64 לאמולטורים ובארכיטקטורת ה־runner לסימולטור; אין בכך בדיקת מכשיר ARM פיזי.

## מצב Native זמני ב־Android

DATA-003 מוסיף את WebViewStateCache לצד MainActivity. מצב WebView אטום נשמר ב־AtomicFile בתוך cache פרטי, עד 8MB לצילום, עם בדיקת פורמט, גיבוב וזהות OS/app/provider. חבילת המערכת נושאת UUID ו־SHA בלבד. נשמרים ארבעה צילומים רגילים אחרונים. קובץ חסר, פגום או לא תואם נפסל, והקורא משתמש במצב הקריאה הלוגי שנשמר בנפרד. זה אינו פורמט הגיבוי הנייד ואינו מייצא מידע. נתוני Parcel זמניים במכוון ואינם נטענים לאחר שדרוג היישום או המנוע.
