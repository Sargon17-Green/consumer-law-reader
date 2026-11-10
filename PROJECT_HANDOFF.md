# כניסה לפרויקט והמשך עבודה

זהו **Sargon17-Green/consumer-law-reader** בלבד: קורא חוק הגנת הצרכן, התשמ״א–1981, Android WebView, SwiftUI/WKWebView ו־Web/PWA משותף. המטרה: מוצר יציב, בטוח, נגיש ומותקן; מפרסמים ערוץ בשל מוקדם וממשיכים בפיתוח. אין תלות בהיסטוריית שיחה.

## קריאה וענף עבודה

1. [מצב](IMPLEMENTATION_STATUS.md), [תקלות](KNOWN_ISSUES.md), [עדיפויות](BACKLOG.md).
2. [קטלוג62 דרישות](docs/requirements.json), [טבלת הדרישות](PRODUCT_REQUIREMENTS.md), [ארכיטקטורה](ARCHITECTURE.md), [החלטות](DECISIONS.md).
3. [בדיקות](TESTING.md), [הפצה](RELEASE_PROCESS.md), [פעולות חיצוניות](EXTERNAL_ACTIONS.md), [דוח שיפורים ומטריצה](docs/MOBILE_ENGINEERING_2026-11-08_HE.md).

ממשיכים מ־**head של PR11 בענףfix/pastafari-date-android-20261028**, לאחר רענון GitHub/ענפים/CI. baseline main016b3de352dabe97f51b34b78ff803965b6cd40d; קוד1.3.9-dev/code17 ו־iOS1.3.9/build17. docs/mobile-release-evidence-20261110 שומר checkpoint המשך, כולל תיקונים שטרם קיבלו קבלה משולבת. אין לדרוס עבודה מקבילה. ניסויי האבחון בענפי work/* משמרים ראיות; אין להעביר דגלי rendererOnly/printOnly או workflows אבחון למוצר.

## פורסם ואומת

- **Web/PWA תיקון2** ב־[reader](https://sargon17-green.github.io/consumer-law-reader/reader/), sourcec3e9d9e5a62454b2d6e857476aae284c093cefef בענףrelease/web-reader-1.3.9-preview. Pages42766006491 ופרסום42765882923 completed/success;75HTTP/SHA כולל owner/alpha/APK. [ראיה קבועה](qa/mobile-2026-11-08/public-web-patch-http-verification.json). ניתן להוסיף למסך הבית; זו התקנת Web ולא IPA Native.
- **הקבלה המלאה האחרונה על706a3bc19f7a75026ccb2bac614816e12c5f5293**: [Linux42764913617](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42764913617) כל9jobs עברו; [iOS42764913616](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42764913616) כל4jobs עברו. tree539895887cecddd5c497f4aea8cf1dd1dc6ff1d5 זהה ל־merge-ref ed7494e0a1fd2c3c2ae80f6929456e30872beaef. [Linux summary](qa/mobile-2026-11-08/acceptance-706a3bc-linux.json), [iOS summary](qa/mobile-2026-11-08/acceptance-706a3bc-ios.json).
- **Android ציבורי1.3.5-beta בלבד** ב־[latest.apk](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk); המפתח הפרטי המקורי אינו נגיש. iOS: סימולטורים ו־unsigned device archive, ללא IPA/TestFlight. אין לפרסם Debug כשדרוג.

## התיקונים המשולבים והצעד הבא

1. להריץ/לעקוב אחרי CI המועמד המשלב SEARCH-005, הצהרת orientations של iPad, בדיקת Windowed Apps, renderer termination ו־collector פרטי. אין לייחס לו PASS של706.
2. iPad Issue13 שוחזר: orientations חסרים גרמו scaling44→30.9pt. תיקון metadata בלבד עבר בניסוי81b5f774510dff6538eff966fae1943f62a28aa3/run42772416090: window אמיתי1032→375pt ו־menu44×44. [ראיה](qa/mobile-2026-11-08/ipad-window-resize-accepted.json). הניסוי התיר auto-scroll בעת tap לתוצאת חיפוש; המועמד המשולב דורש תוצאה נראית לפניtap בעקבות תיקון החיפוש.
3. SEARCH-005 שוחזר ב־DOM מלא ללא רשת: raw scroll לא מתאים לאחר שינוי רוחב/גובה. התיקון מעגן תוצאה נבחרת ומגביל offset לאזור הנראה. tests/search_state_qa.py בודק5רצפים כולל גובה בלבד וחזרה חוזרת. קובצי before/after-local תחתqa מתעדים סביבה ו־dirty source; רק ריצתCI completed תבסס קבלת המועמד. אחרי שערי Web לפרסם תיקון3 עצמאית.
4. Android: run-as אינו מורשה ל־QA APK שאינו debuggable. collector חדש משתמש ב־ADB root רק באמולטור userdebug אחרי הבדיקה, SELinux enforcing,7שמות whitelist, stat/סוג/גודל/SHA. בלי PDF מיוצא התואם לגיבוב PdfRenderer אין PASS שלAPI36. ניסויc08 הוכיח פונקציית renderer recovery אך נכשל באיסוף בגלל exec-out שיכול להחזיר טקסט שגיאה עם סטטוס0; stat shell-v2 קודם לקריאה מתקן זאת. המועמד המשולב כולל5unit נגד ראיות מזויפות ושחזור שאילתת חיפוש ממשית לאחר renderer termination.
5. אחרי completed PASS לכל השערים המהותיים: לעדכן קטלוג/ראיות/Issue13, להסיר draft ולמזג PR11 אם מדיניות המאגר מאפשרת. לא לעקוף הגנות environment. פרסום Web משמר כל מה שמחוץreader, marker commit/tree ו־75GET; release branch חייב fast-forward ללא force. הוראות RELEASE_PROCESS.
6. להמשיך BACKLOG אחרי הפרסום. כל מחזור נשמר בענף מרוחק, עם בדיקות, תוצאות ו־handoff מעודכן. ארטיפקטים זמניים; סיכומי SHA, run/job/source ומגבלות נשמרים ב־qa. אין לעצור בגלל pending CI.

## גבולות עבודה

SHA256 המקור המשפטי **de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9**, תאריך אימות **2026-10-28**. verify_release.py חייב להעביר35בדיקות exactSHA/DOM/מקורות/IDs/קישורים. אין בדיקה או שינוי משפטי. לשמר שם מלא/RTL/נושאים/היסטוריה/העתקה/מקורות/הערות/תאריך/גיבוי/Word/שיתוף/Print. אין Analytics/ענן/פרסומות או שירות חדש.

תיקון רגיל, QA, PR, אבחון, מיזוג ופרסום שעברו שעריהם מורשים אוטונומית. אין force-push, שינוי מפתח שדרוג, החלפת APK ציבורי ב־Debug או טענות בדיקה פיזית/חתימה/חנות ללא ראיה. מפתח חתימה מקורי, Team/ASC, תשלום/תנאים, זכויות ומכשיר שאינו נגיש הם פעולות חיצוניות בלבד; EXTERNAL_ACTIONS מפרט מה הוכן ומה חסר. אין צורך בחבילת Windows או בהרצה במחשב המשתמש.
