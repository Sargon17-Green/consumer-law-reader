# מחזור ההנדסה למובייל — תוצרים וראיות

עודכן ב־10.11.2026. **בטא Web/PWA1.3.9-dev פורסמה** ב[קישור הקבוע](https://sargon17-green.github.io/consumer-law-reader/reader/), תיקון2 עם75 בדיקות HTTP/SHA256 שעברו ושימור alpha וה־APK הציבורי. Native Android/iOS לא פורסמו במהדורה חדשה: חסרות חתימות מקוריות; קבלתAPI36 עברה706, וקוד ההמשך דורש רגרסיה נפרדת. מצב מתעדכן לפי [IMPLEMENTATION_STATUS](../IMPLEMENTATION_STATUS.md); כל דרישה רשומה ב־[PRODUCT_REQUIREMENTS](../PRODUCT_REQUIREMENTS.md).

העבודה ממשיכה את [PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11), על בסיס main016b3de352dabe97f51b34b78ff803965b6cd40d. נבדקו12ענפים, PRs1–11, Issue7, היסטוריית commits/Releases ו־Actions; תיקונים תקינים שכבר מוזגו לא יושמו מחדש. PR1 הוא ביקורת ישנה ולא מקור ממצאים אוטומטי.

`original/Consumer_Protection_Law.html` נשאר זהה בביטים: SHA256de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9. תאריך אימות2026-10-28, הערות, אסמכתאות ומעמד משפטי לא שונו. verify_release משווה DOM/kישורים/IDs/footer/מקורות ומשאבים; alias של PEGI מוחזר לפני ההשוואה. לא נעשתה בדיקה משפטית. NOTICE_HE לא שונה.

## שיפורים ממומשים

קיצורי commit בטבלה מפנים להיסטוריית [PR 11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11/commits). ״בדיקה קיימת״ מתארת את תרחיש האימות; קבלת מועמד תלויה בטבלת הריצות בהמשך.

| מזהה | פלטפורמה | הבעיה והסיבה | התיקון והקבצים | בדיקה מאמתת | תוצאה/כיסוי | commit |
|---|---|---|---|---|---|---|
| S01 | משותף | היסט מנורמל שימש לחיתוך מחרוזת מקור שאורכה שונה | `mobile-core.js`, `mobile.js`, `mobile-sources.js`: מיפוי UTF-16 מדויק; טיפול בניקוד, טעמים, ציטוטים, מקפים ורווחים | 500 מקרי Unicode + סימון DOM + שני מנועי WebView | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b` |
| S02 | משותף | חיפוש מנורמל לא הבחין בהתאמה מילולית | מצבי התאמה/סינון, קטעי הקשר בטוחים, query עד 512 ותוצאות במנות | חיפוש→סעיף→תוצאות, קלט HTML עוין, אינדקס 581 יחידות | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b` |
| D01 | משותף | שחזור iOS רחב לפי תחילית; לא הייתה החלפה מאומתת משותפת | schema 2, whitelist, בדיקת יעדים/מעגלים/גודל, preview, אישור ויומן rollback ב־core/settings | round-trip, legacy, quota, crash recovery, unrelated keys | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b`, `5e68bb6` |
| D02 | Android | לא היה גיבוי Native מלא | SAF CreateDocument/OpenDocument עם IO ברקע וללא הרשאת אחסון | קובץ נוצר ונקרא דרך ממשק Android; העדפה משוחזרת רק אחרי אישור | קבלה API31; תרחישים נוספים לפי known issues | `739871b`, `833c5ff` |
| D03 | Android | גיבוי גדול נשמר כמחרוזת ב־Activity Bundle ועלול לחרוג ממגבלת Binder | קובץ פרטי אטומי, דגל קטן ב־saved state, ניקוי וביטול כפילויות | גיבוי גדול תקין, saved state קטן, יצוא/יבוא SAF | קבלה API31; תרחישים נוספים לפי known issues | `a9a5e7d` |
| D04 | Web/Android | פענוח UTF-8 יכול היה להחליף בתים פגומים בלי לדחות קובץ | decoder מחמיר; iOS כבר דוחה UTF-8 פגום | בחירת קובץ פגום אינה מציגה אישור ואינה משנה העדפות | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `a9a5e7d` |
| SEC01 | משותף | שוחזרה הרצת script בתוך srcdoc תחת מדיניות unsafe-inline | CSP בתחילת head עם hashes דטרמיניסטיים לסקריפטים/handlers המקוריים | ניסיון iframe script אינו רץ ב־Chromium/Android/WKWebView | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `fd66d43` |
| SEC02 | שתי המעטפות | גבולות משאב/גשר לא היו מכוסים מספיק | מסמך מקומי בלבד, נתיבים תחומים, URL/query validation, מסגרות חסומות; אימות main frame ומקור ב־iOS | URL עוין, מסגרת, משאב לא מורשה, מסמך אחר | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b`, `fd66d43` |
| N01 | משותף | קישורים שותפו לנתיב ציבורי שלא הבטיח ממשק נייד/יעד | נתיב `/reader/#…`, קידוד fragment ובדיקת יעד; iOS מעדיף סעיף נראה | URL משותף מדויק ובדיקת בעלות נתיב פריסה | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `6d014db`, `833c5ff` |
| N02 | משותף | חזרה ומחזור חיים לא שימרו תמיד את מצב הקריאה/חיפוש | צילום גלילה בהיסטוריה, session מקומי, שחזור חיפוש ומיקום, focus ו־Escape | Back אמיתי, reload, תהליך חדש ורצפים ארוכים | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b`, `6d014db` |
| N04 | משותף / WK | שחזור פיקסלים אחרי שינוי גופן הציג סעיף אחר; גלילת Native יכלה לדרוס את שחזור Back לאחר פריים נכון זמני | חתימת פריסה בנקודת הקריאה; שחזור לסעיף בפריסה שונה; תיקון מאוחר שנעצר בפעולת משתמש | בדיקת סעיף נראה ושיתוף מדויק אחרי reload, ו־Back יציב אחרי 600ms | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `a9a5e7d` |
| N03 | Android | Back מודרני וטעינת Renderer לא טופלו במלואם | OnBackInvokedDispatcher, error/retry, renderer recovery | Back Native, API 31/36, Ready אמיתי | קבלה API31; תרחישים נוספים לפי known issues | `6d014db` |
| DATE01 | שתיהן | רכיב תאריך נחסם ב־CSP/מדיניות Native | שלושה נתיבי HTTPS JSON בלבד; Android CORS, גבולות נפח וזמן, ללא redirects; WK raw בלבד | fallback מבוקר, ישן/פגום/כשל, תאריך חי כשמקורו עדכני | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b`, `5e68bb6` |
| A01 | משותף | overflow במסך צר ובטבלאות המשמשות פרוזה | תיקון תצוגת שורות ממוספרות בלי שינוי הטקסט, עטיפת טבלאות נתונים | 320–1180px וגופן 28 | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `fd66d43`, `1a4982b` |
| A02 | משותף | נמצאו ליקויי contrast, כפתורים מקוננים והחזרת focus | תיקוני צבעים/מצבי ניגודיות/תפקידים/מטרות 44px ודיאלוגים | axe אוטומטי בכמה מצבים ורוחבים; keyboard ו־Escape | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `1a4982b`, `5e68bb6` |
| A03 | iOS / Web | מסגרת הנגישות של אייקוני Native נשארה קטנה אף שהוקצה להם שטח חיצוני; הגדרות Web קיבלו שם נגיש זהה | אזור 44×44 בתוך label ו־contentShape; שמות הגדרה הכוללים את המונח | מדידת frame ב־XCUITest ושמות מובחנים ב־DOM | PASS בסימולטורים; אין הפצה חתומה | `aa9f826` |
| P01 | משותף | מימוש מיפוי מלא לכל אות גרם רגרסיית אינדוקס פי 4 | נרמול מחרוזת מהיר לאינדקס; המיפוי נבנה רק לקטעי תוצאה | מדידה השוואתית מאמצע המחזור ומטמון אינדקס קבוע | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `1a4982b` |
| IO01 | Android/iOS | פתיחת קובץ/שיתוף היו חסרים כיסוי Native אמיתי | ספק קובץ לקריאה בלבד וכתיבה אטומית, cleanup, שיתוף סעיף נראה; הדפסת iPad עם עיגון | מקבל קובץ ב־UID אחר משווה SHA; WK משווה bytes; Clipboard אמיתי | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b`, `833c5ff` |
| PUB02 | Android / CI | checksum של נכס Release לא הוכיח חתימה המתאימה לשדרוג | אימות apksigner ותעודת ההפצה לפני עדכון latest.apk | APK ציבורי אמיתי מתקבל ו־Debug אמיתי נדחה | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `a9a5e7d` |
| IO02 | Android / משותף | מיליוני בתים של UTF-16 יכולים לחרוג ממגבלת Binder; הממשק הודיע הצלחה לפני השלמת Native | גבול IPC שמרני, טיפול בכשל, אישור Native והצגת מלוא הטקסט לבחירת חלקים כאשר הבחירה גדולה מדי | Parcel אמיתי מעל 1MB; דחייה בלי קריסה או החלפת הלוח; fallback שומר 600,000 תווים | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `2167a9e` |
| CI01 | CI | היו רק build/smoke Native, ללא שימוש משמעותי | Instrumentation, XCTest/XCUITest, שדרוג וראיות לכשל; Xcode 26.3 | אמולטורים וסימולטורים, xcresult/logcat/screenshots | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `739871b`–`833c5ff` |
| CI02 | CI | כלי build/actions לא היו מקובעים ומאומתים דיים | SHAs ל־Actions, digest לכלי Android, סריקת Gitleaks מלאה ומוגנת חשיפה | התאמת digest, בדיקת APK, סריקת כל היסטוריית Git | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `6d014db`, `5e68bb6` |
| BUILD01 | משותף | קבצי עריכה לא קשורים ופלט ישן יכלו להיכנס לחבילה | רשימת סוגי משאבים והדרה של קבצים זמניים, בנייה נקייה | שתי בניות זהות עם קובץ זמני ופלט מיושן ביניהן | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `a9a5e7d` |
| PUB01 | Web | workflow הישן עלול היה לדרוס אתר alpha 0.17 בקוד ישן | העתקת gh-pages קיים, שינוי reader בלבד ובדיקת גיבובי שאר האתר | `test_reader_site.py`, דוח preservation | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `6d014db` |
| DOC01 | שתיהן | חסרו תיעוד גיבוי נייד וגילוי תקשורת ברור | מדיניות מקומית נגישה/דף ציבורי, דוח זה, תיעוד התקנה/משוב/חנויות | התאמת תוכן המדיניות בשני היעדים ו־axe לדיאלוג | מומש; פרסום Web ו־Native לפי טבלת הקבלה | `a9a5e7d` |
| A04 | משותף | טבלאות אנונימיות/טפסים והזחות font48 גלשו או נחתכו | prepareReadingTables ו־flex מסתגל; מיכלי נתונים דו־ממדיים נגישים | 66תקנות × 4גופנים × 6רוחבים; WebView/WK | PASS בפריסה; פורסם Web | `1f45215` |
| DATE02 | Native | query/path מנורמלים הותירו alias לא קנוני וב־Android opaque URL עלול לזרוק חריגה | בדיקת encoded path/query, duplicates/length; ללא שינוי אלגוריתם | 57מקרי Android ומקרי Swift עוינים | PASS ב־API31 ובסימולטורים; scope לפי logs | `6d2b540` |
| PUB03 | Web | המימוש המשותף לא הגיע למשתמשים | פרסום reader/ עצמאי ושמירת alpha/APK; source marker וגיבובי נכסים | HTTP identity/no redirects,74קבצים מדויקים | פורסם בפועל; workflow deploy branch נדחה בנפרד | `83fe5ec` |

## מטריצת פלטפורמות

| יכולת | Android | iOS | אימות/הבדל שנותר |
|---|---|---|---|
| טקסט עברי/RTL, שם מלא, תוכן עניינים וחקיקת משנה | משותף | משותף | גיבוב + DOM; אין שינוי משפטי |
| חיפוש מדויק/מנורמל, ניקוד ומיפוי סימון | משותף | משותף | Node/DOM/WebView/WK |
| נושאים, קישורים, סדר והסתרה | אחסון מקומי | אחסון מקומי | topic QA, export/restore ומעבר גרסה ב־Android |
| חזרה, מיקום קריאה וחיפוש אחרון | מערכת + היסטוריית Web | מחוות WK + היסטוריית Web | שחזור אינטראקציות; אין יומן ענן |
| גיבוי ושחזור | SAF | Files + native confirmation | אותו schema; ממשקי מערכת שונים |
| שיתוף קישור | Android Sharesheet | UIActivityViewController | אותו נתיב ציבורי ויעד |
| העתקה | ClipboardManager | UIPasteboard | בדיקה Native; אין משלוח לשרת |
| הדפסה / PDF | Android Print Framework | UIKit Print | לא נבדקו מדפסת פיזית ותוצאת כל דרייבר |
| Word מצורף | ContentProvider והרשאת URI | שיתוף URL מתוך החבילה | בדיקת bytes; לא רינדור Word חיצוני |
| תאריך חיצוני | proxy נתיבים מוגבל + CSP | WK resource rules + CSP | אלגוריתם המקור נשמר |
| גודל טקסט/ניגודיות/Reduce Motion | Web + fontScale | Web + Dynamic Type | הגדלה ידנית גוברת על ברירת המחדל המערכתית |
| קריאה בלי רשת | משאבים ארוזים | משאבים ארוזים | Android ניתוק אמולטור; WK חסימת משאבים/קריאה מקומית |
| קישור נכנס ליעד בדפדפן | URL ציבורי | URL ציבורי | אין App Links/Universal Links מאומתים; לא נרשמה בעלות דומיין חדשה |
| הפצה ציבורית חתומה | 1.3.5-beta הקיימת | לא קיימת ראיית TestFlight | חסרים מפתח Android המקורי וחשבון/חתימת Apple |

## דוח בדיקות וקבלה

| מקור/סביבה | תוצאה מאומתת | ראיה ומגבלה |
|---|---|---|
| 2f91d12, Linux/Python3.12/Node22 | 40unit tests,500Unicode, schema/rollback, date fallback, source35checks, Gitleaks עברו | [42683016176](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016176); הריצה הכוללת נכשלה ב־Native |
| Chromium375/320/430/768/1032/1180 | 268בדיקות חוק/66תקנות בכל רוחב,0חריגות אחרי התיקון;32axe scans בארבעת רוחבי CI עברו | [before/after](../qa/mobile-2026-11-08/horizontal-layout-before-after.json); viewport מדומה, לא מכשיר פיזי |
| Chromium ServiceWorker אמיתי | cache38נכסים, reload/search/סעיף14 ומיקום Home start URL ללא רשת עברו | [pwa-offline](../qa/mobile-2026-11-08/pwa-offline.json); loopback trusted origin, לא התקנת טלפון |
| Android31 | התקנה, upgrade QA, restart, online/offline, חיפוש, Clipboard, Word, Share ו־SAF עברו | [job129382997932](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016176/job/129382997932); מפתח QA אינו המקורי |
| Android26 | כל הזרימה המקוונת והמנותקת עברה באבחון עם pointer לפי filename bounds | [42685860051](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42685860051), API26job עבר; Android36job נכשל; AOSP133/RRO מתועדים |
| Android36 | build/AAB/התקנה ורוב התרחישים עברו; אין PASS לשמירת PDF מערכתית מלאה | QA-ANDROID36-PRINT ב־KNOWN_ISSUES; אין פרסום Native חדש |
| iPhone26.2/iPad26.2/iPhone18.5/iPhone16.0 | ארבעה jobs הסתיימו success; XCTest/WK/XCUITest, אייקון קבוע, share/print/cancel/files/lifecycle | [42683016332](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016332); Apple audit לכותרת Native17+ בלבד, iOS16תפקודי עבר |
| Web ציבורי source83fe5ec | כל74קבציHTTP תואמים SHA256, כולל alpha ו־latest.apk | [HTTP proof](../qa/mobile-2026-11-08/public-web-http-verification.json); build ב־run42718069159עבר, deploy branch נדחה ב־environment; פרסום gh-pages הרגיל מאומת בפועל |

checkout של PR היה d178bb6d1765707732e9ad8f5ed448a1de5ebac3/treecadba5f98945b5b122f87ffcecd1455a63f9d2f1, זהה לקודhead2f91d12. תוצרים נושאים sourceCommit/tree/dirty ואין לכנות merge-ref של PR בשם head. ראיות ביניים קודמות אינן קבלה לקומיט חדש; פירוט כשל GitHub500 ו־b7d8168 נמצא בקובץ [ביניים](../qa/mobile-2026-11-08/b7d8168-interim-evidence.json).

## אבטחה ונגישות

שוחזרה ונחסמה הרצת srcdoc תחת unsafe-inline; ה־CSP מבוסס hashes, ללא unsafe-eval. כתובות/קבצים/גשרים תחומים; שדות JSON/Unicode/נפח/UTF-8 ותתי־מסגרות נבדקו. Android INTERNET בלבד; אין SDK איסוף, חשבונות או סנכרון. סריקות Gitleaks/npm/static הן ראיות בתחום הסריקה, ולא הוכחת העדר כל פגיעות. היסטוריה לא שוכתבה וסודות לא פורסמו.

תוקנו contrast, focus, תפקידים, תוויות, מקלדת, targets44px, RTL, טבלאות ו־Reduce Motion. 32סריקות axe וה־Apple Native audit עברו בתחום המוצהר. אין טענת WCAG/VoiceOver/TalkBack אנושיים מלאה או בדיקה פיזית. מדיניות הרשת והפרטיות ב־web/privacy.json וב־reader/privacy.html.

## ביצועים

לפני אופטימיזציית הנרמול הראשונית נמדדה רגרסיית אינדוקס פי4 ונשללה. חזרנו לנרמול מהיר לאינדקס ומיפוי מקור רק ל־snippet. שלוש חזרות השוואת baseline016b מול המימוש הקודם שמורות ב־[performance](../qa/mobile-2026-11-08/performance-before-after.json); אין טענת שיפור כולל בזמן פתיחה ממדגם קטן.

אחרי תיקון הרוחב בוצעה השוואה נפרדת מולb7d8168: Chrome157,375×812,שלושה contexts טריים בכל מצב. חציון פתיחה רגילה1216.54→1208.62ms, אינדקס101.3→99.2ms,100שאילתות9.6→8.9ms. בהאטתCPUסינתטית×4: פתיחה3843.37→3759.61ms, אינדקס465.7→479.7ms, שאילתות52.8→45.8ms. אלו מדידות מקומיות עם תקורת אוטומציה, ללא מובהקות סטטיסטית וללא טענה למכשיר חלש פיזי. [כל הדגימות](../qa/mobile-2026-11-08/layout-performance-before-after.json).

Native מודד PSS/CPU של תהליך היישום ו־XCTest reading gestures בשלוש חזרות. אין לייחסם לסך כל תהליכי WebKit/Chromium או למדידות חומרה פיזית. פירוט CPU/זיכרון/xcresult בארטיפקטים; Split View מלא ו־sustained low-memory נשארים במעקב ולא מסומנים PASS.

## מועמדים ופעולות חיצוניות

Android1.3.9-dev/code17: Debug מאומת, unsigned APK מיושר ו־AAB לא חתום; public1.3.5-beta נשמר. APK הציבורי SHA2562772e3d8195de2d9a66edc8cdbc9e0940ac71f8cb55f1597dcc7c122120101af. בדיקת upgrade היא עם עותק בטא במפתח QA, ולא הוכחת שדרוג במפתח המקורי. אין להפיץ unsigned/Debug כשדרוג.

iOS1.3.9/build17: ארבע בניות סימולטור ומבחנים עברו; מסלול device archive לא חתום הוכן. אין IPA חתום, TestFlight, אישור חנות או בדיקת iPhone פיזי. Web1.3.9-devפורסם בנפרד, ניתן להוספה למסך הבית, ואינו Native.

החסמים היחידים הדורשים גורם חיצוני: המפתח ההיסטורי של Android, גישת Apple Team/profiles/ASC, מכשיר/ציוד פיזי שאינו זמין, והצהרות בעל זכויות/חשבון. הפרטים והצעדים הקצרים ב־[EXTERNAL_ACTIONS](../EXTERNAL_ACTIONS.md). כל שאר העבודה פתוחה ב־[BACKLOG](../BACKLOG.md) והכניסה העצמאית ב־[PROJECT_HANDOFF](../PROJECT_HANDOFF.md).

## מחזור המשך10.11 — קבלה משולבת נדרשת

| שיפור | פלטפורמה | ממצא וסיבה | מימוש | בדיקה וראיה | מצב |
|---|---|---|---|---|---|
| SEARCH-005 | משותף | raw pixel scroll אינו מתאים לתוצאות שעברו reflow או לגובה חלון חדש | web/mobile.js: target נבחר+offset+layout, תחום נראה; באותה פריסה offset נשמר | tests/search_state_qa.py; before/after-local תחתqa |5רצפים מקומיים עברו;CI/פרסום ממתינים |
| NATIVE-003 | iOS | Info.plist חסר orientation flags, windowing scaled44pt→30.9pt | ios/project.yml:3iPhone/4iPad; raw-plist XCTest + ReaderWindowingUITests | run42772416090/job129683054613,artifact13742524176 | ניסוי אמיתי עבר; רגרסיה משולבת נדרשת |
| QA-PRIVATE | Android | run-as אינו מורשה; raw exec-out עשוי להחזיר שגיאה עם status0 | scripts/collect_android_private_evidence.py: emulator/root/stat/bounds/magic/SHA; run_android_emulator_qa.sh שומרכשל |5unit כוללPNGכוזב/PDFשונה/physicalrefusal; fullCI ידרושexportedPDF | מימוש, ללאPASSריצהכוללתחדש |
| QA-RENDERER | Android | כשל תהליךrenderer לא נבדק ברגרסיה | ReaderInstrumentation ציבוריterminate, NativeRecovery/NewActivity/Ready/section/font/query | ניסויc08 functional31/36 עבר אך overallFAIL collector; בדיקהחזקה יותר משולבת | רגרסיה משולבת נדרשת; לאOOM |
| CI-004 | CI/iOS | PR paths החסירוmetadata/fixtures/dependencies | ios-ci.yml רשימותpush/PRתואמות | unit/build ו־4סימולטורים עלהמועמד | מימוש; קבלהמשולבתנדרשת |

מסמכי מצב/קטלוג/העברה עודכנו תוך הסרת טענות pending ישנות. מזההcommit של כל שינוי יופיע בהיסטוריית PR11; אין למלא SHA עתידי או להסיקPASSמהימצאותהבדיקה.
