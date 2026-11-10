# בדיקות ותנאי קבלה

הפקודות מיועדות ל־Work/Linux/CI או ל־Mac פיתוח קיים, ולא לחבילת התקנה על מחשב Windows של המשתמש. פרטים ותבנית משוב: [docs/MOBILE_TESTING_HE.md](docs/MOBILE_TESTING_HE.md).

```bash
python3 -m venv .qa-venv
. .qa-venv/bin/activate
python -m pip install -r requirements-qa.txt playwright==1.57.0
python -m playwright install chromium
npm ci --prefix tests/qa --ignore-scripts
python scripts/build_web.py
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/mobile_core_qa.js
node tests/pastafari_widget_qa.js
python scripts/verify_release.py
python scripts/mobile_security_audit.py
python scripts/run_secret_scan.py
python tests/technical_smoke_134.py
python tests/topic_navigation_qa.py
python tests/mobile_integration_qa.py
python tests/pwa_offline_qa.py
python tests/search_state_qa.py
python scripts/validate_project_docs.py
```

`LAW_QA_WIDTH` יכול לבחור320/430/768/1180; `LAW_QA_CHROMIUM` מצביע על Chrome מקומי מאומת אם ה־CDN של Playwright אינו זמין. אין להריץ בדיקת rebuild ו־browser על אותה dist במקביל. unit tests אחדים בונים dist מחדש לצורך בדיקת שחזוריות.

ה־DOM המלא והסקריפטים האמיתיים נבדקים, כולל 581 יחידות חיפוש; fixture המדידה `tests/fixtures/reader_layout_probe.js` משותף ל־Chromium, ל־Android WebView ול־WKWebView, ונארז רק בחבילות הבדיקה. בדפדפן: כל66 התקנות × ארבעה גדלי גופן, root overflow ושימוש בטבלאות גלילה; כותרות נושאים/קישורים באורך90 נוצרות לפני init כדי שהבדיקה אינה ריקה. axe: שמונה מצבים × ארבעה רוחבים. אלו אינם אישור WCAG מלא או בדיקת קורא מסך אנושי.

Android: `.github/workflows/ci.yml` בונה ומתקין Debug, QA instrumentation, ועותק APK ציבורי בחתימת QA מוצהרת לצורך שדרוג. API26/31/36; API36 משתמש ב־APK מתוך AAB. `scripts/run_android_emulator_qa.sh` מריץ actual online/offline, תהליך חדש, תאריך, חיפוש, Back, סיבוב, Clipboard, Word cross-UID, SAF, print ושימוש חוזר. API26 דורש סביבת בדיקה AOSP WebView133 ורכיב RRO בעל משאב אחד עם SELinux enforcing; אין שינוי בבתיו של ספק ה־WebView ואין כיבוי SELinux. זו אינה תמונת retail ללא התאמות.

iOS: `.github/workflows/ios-ci.yml`, Xcode26.3/macOS15, iPhone26.2/iPad26.2/iPhone18.5/iPhone16.0. XCTest ו־XCUITest בודקים WK פעיל, גשר זר/child-frame, קובץ גיבוי, print, share, lifecycle, סיבוב ואייקון Home Screen. audit Native זמין מ־iOS17 ומוגבל לכותרת; iOS16 אינו מדולג במבחן התפקודי. workaround של libswiftWebKit ב־18.5 ו־bootstrap ב־16 מתועדים ב־workflow, לא שינוי מינימום מערכת.

שער Web עצמאי: source hash/DOM, Node/backup/date/security, ארבעה browser jobs ומטמון offline, שימור alpha ו־APK, ולאחר פרסום השוואת כל הבתים ב־HTTP. כשל Native שאינו מופעל ב־Web אינו הופך את מבחני Web לכושלים; הכשל חייב להישאר גלוי ומתועד.

שער Native: בדיקות הפלטפורמה על אותו checkout/tree, חתימה נכונה לשדרוג, בדיקות חבילה והתקנה/שדרוג; אין שחרור ציבורי Debug/unsigned או סימולטור. קבלה מלאה אינה מבוססת רק על קומפילציה, צילום מסך, ניסיון חיצוני או jobs שטרם הסתיימו. logs/artifacts מוגבלים בזמן; סיכומים חתומים בגיבוב ומזהי run/commit נשמרים ב־qa/ ובמסמכי הפרויקט.

## רגרסיות שנוספו ב־10.11.2026

`tests/pwa_offline_qa.py` מפעיל ServiceWorker אמיתי במקור loopback מאובטח ובהתאמת reader/; לאחר activation מנותקת כל הרשת, מבוצעים reload/search/14/פתיחה חדשה, ואז נמחק CSS חובה ומוסף נכס זר. מספר38 הרשומות נשאר קבוע אך מוכנות חייבת להיכשל ולהופיע בלוח ההתקנה. `reader_layout_probe.js` בודק גם סעיף וחלק בתוספת מתחת לכפתור חזרה בפועל אחרי focus. `test_public_reader.py` דורש owner marker ומונע PASS על redirect/bytes ישנים. בניסוי Print נדרש עמוד preview ולא רק enabled/visible; קובץ PDF אמיתי עדיין נבדק ב־PdfRenderer. אין טענת מכשיר פיזי.

ראיות Android QA נשמרות ב־files הפרטי ונאספות רק באמולטור userdebug מורשה, עם SELinux Enforcing. run-as אינו זמין בחבילת QA שאינה debuggable ואין להסתמך עליו. PDF שהמשתמש שמר בפועל דרך Print/SAF נקרא כזרם תחום32MB ונבדק ב־PdfRenderer וב־SHA256; אין shell cp או screenshots ב־FUSE. ניסוי4819 עבר ואומת גם בהורדה עצמאית של חמשת הקבצים. רגרסיה משולבת נדרשת לפני מיזוג.

רגרסיות10.11: search_state_qa.py מריץ5רצפי full-DOM ללא רשת (רוחב/גובה/אותה פריסה וחזרה חוזרת). בדיקת Windowed Apps ב־ReaderWindowingUITests משנה את חלון המערכת של iPad26.2 עם pointer על resize-grabber שנצפה; אין CSS-mock. היא מדולגת במפורש ב־iPhone, ששאר בדיקותיו רצות. ReaderPolicyTests קורא raw Info.plist של האפליקציה הבנויה, ולא infoDictionary שממזג device override. Android API29+ עוצר renderer אמיתי דרך API ציבורי, דורש חלון פתיחה מחדש, Activity/WebView חדשים ו־Ready עם גופן/סעיף/שאילתה. API26 אינו מקבל PASS ל־API שאינו קיים בו. זה אינו עומס זיכרון או OOM פיזי.

איסוף Android הפרטי פועל אחרי התרחיש ורק באמולטור המזדההqemu=1/UID0/SELinux Enforcing. יש whitelist קבצים ואין שינוי בהרשאות המוצר. stat shell-v2 לפני exec-out מונע שמירת שגיאות ADB כתמונות; PNG/JSON/PDF נבדקים. API36 מחייב PDF שגיבובו תואם ללוג PdfRenderer Native. trap שומר את exit status המקורי וגם מכשיל ריצה שהצליחה תפקודית אך לא סיפקה את הראיות הנדרשות. tests/test_android_evidence.py בודק5מקרי קבלה/סירוב.

DATA-003 regression creates60 actualChromiumhistory entries with bounded deterministic state, measuresrawWebView>1MB and actualActivityBundle<50KB, recreatesActivity, checks history/index andNativeBack/Forward, and rejects missing/corrupt/path-traversal cache references. Additional final-regression cases cover stale reference digests, tampered payload, wrong installation signature and8MB read/write bounds while preserving the accepted snapshot; these cases were added after4819 and must execute in combined CI. OpaqueParcelcache is ephemeral and never portable acrossOS/app/provider installations. Durablepreferences/search/lastread remain separate;8MBsnapshot bound and4normal recent snapshots. This is independent of the portable settings-backup schema.
