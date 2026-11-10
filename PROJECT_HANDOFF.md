# כניסה לפרויקט והמשך עבודה

**Sargon17-Green/consumer-law-reader** הוא קורא חוק הגנת הצרכן, התשמ״א–1981: Android WebView, SwiftUI/WKWebView ו־Web/PWA משותף. אין לערבב עם פרויקט לוח השנה. מפרסמים ערוץ בשל מוקדם וממשיכים; המידע במאגר ובקישורים מספיק ללא שיחה.

## לקרוא תחילה

[מצב המימוש](IMPLEMENTATION_STATUS.md), [63 הדרישות](PRODUCT_REQUIREMENTS.md), [הקטלוג](docs/requirements.json), [BACKLOG](BACKLOG.md), [תקלות](KNOWN_ISSUES.md), [ארכיטקטורה](ARCHITECTURE.md), [בדיקות](TESTING.md), [הפצה](RELEASE_PROCESS.md), [החלטות](DECISIONS.md), [פעולות חיצוניות](EXTERNAL_ACTIONS.md).

## מה פורסם ומה התקבל

- **Web/PWA תיקון3 פורסם:** [reader](https://sargon17-green.github.io/consumer-law-reader/reader/), ניתן להוספה למסך הבית. מקור cca785ed8b1f3d4c96bf25c0eb50e77b04899566, מטמון453decfde812ec9b. [42778620385](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42778620385) completed success;75 HTTP/SHA עברו כולל alpha/APK. [ראיה](qa/mobile-2026-11-08/public-web-patch3-http-verification.json).
- **Android הציבורי1.3.5-beta:** [APK קבוע](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk). אין מפתח היסטורי נגיש שאומת; חיפוש ממוקד תועד. מועמד1.3.9-dev/code17 Debug/unsigned בלבד. אין להחליף זהות חתימה.
- **iOS1.3.9/build17:** סימולטורים וארכיון מכשיר לא חתום; אין IPA חתום או TestFlight.
- **מועמד94cdf7d:** [Linux42817834059](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42817834059)9/9 PASS; [iOS42817834181](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42817834181)3/5 PASS,2 FAIL בסגירת sharesheet ב־iPhone16/iPad18.5. [ראיה מלאה](qa/mobile-2026-11-08/acceptance-94cdf7d.json). אין למזג מועמד שנכשל.
- Android94 כולל cache עוין ו־IME אמיתי בכל3API online/offline; raw1.6MB→Activity1036–1200bytes, recreate/history/Back/Forward. [PDF146עמודים וחמשת הקבצים אומתו עצמאית](qa/mobile-2026-11-08/android-private-exports-94cdf7d.json). [תצורת1.5GB/ליבה אחת התקבלה בנפרד](qa/mobile-2026-11-08/android-constrained-hardware.json); אין טענת1GB/OOM.
- [iPad26/94 עבר במלואו](qa/mobile-2026-11-08/ipad-window-94cdf7d.json): resize אמיתי1032→375pt,44pt, תפריט/שיתוף וסגירה, selected result נראית לפני tap ושאילתה14. כל38 נכסי Web של94 זהים ל־Web שפורסם; אין צורך בפרסום זהה בגלל שינוי Native.

## ענפים והצעד הבא

1. לרענן GitHub לפני כתיבה. [PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11) בענף `fix/pastafari-date-android-20261028` מרכז את המועמד; `docs/mobile-release-evidence-20261110` checkpoint. בסיס main בעת תחילת העבודה016b3de352dabe97f51b34b78ff803965b6cd40d. אין לדרוס עבודה מקבילה.
2. **העדיפות העליונה:** לקבל את בדיקת סגירת השיתוף בגרסאות הישנות. בענף `work/ios-legacy-share-20261110`,5450373c14100424b2d17358cf2acb54659cbf23, [ריצה42850867489](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42850867489), הבדיקה דורשת Close נגיש בפועל והיעלמות ActivityListView. ניסוי51f נכשל בקומפילציה עקב print element שהסתיר את Swift.print; תוקן. אין להסיק PASS מריצה ממתינה.
3. לאחר קבלה להעביר **רק ReaderUITests.swift** הקבוע והראיות ל־PR11; לא להעביר workflow אבחון. להריץ9Linux/Android ו־5iOS על ראש/tree אחד, עם XcodeGen2.46.0 מקובע. להסיר draft ולמזג רק לאחר completed PASS לכל השערים המהותיים ובהתאם להגנות.
4. לעדכן דרישות/ראיות/known issues/handoff, לשלוח commits ולסגור Issue13/14 רק לפי הקבלה שהוגדרה. Issue7 נשאר לחתימה. אם מיזוג מפעיל Pages, לבדוק את75HTTP מול source marker החדש ולשמר alpha/APK.
5. אחר כך לחתום/להפיץ רק אם מקור המפתח/Team נגיש ומורשה. להמשיך את יתר BACKLOG בלי להמתין לחתימה; אין צורך בהתקנות או סקריפטים במחשב המשתמש.

## חוזים והגבולות

SHA256 המשפטי נשאר `de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9`; מועד האימות **2026-10-28**. verify_release חייב להעביר35 בדיקות SHA/DOM/IDs/קישורים. אין שינוי חקיקה/פרשנות/הערות/תאריכים, ענן, Analytics או פרסומות.

Parcel cache זמני מותנה באותה התקנת OS/app/provider ואינו גיבוי נייד. כשל חוזר למיקום לוגי; נתוני המשתמש נשמרים בנפרד. collector פרטי מורשה רק באמולטור userdebug/UID0/SELinux Enforcing ומאמת בתים בפועל; אין החלשת debuggable.

תיקונים רגילים, בדיקות, PR, מיזוג ופרסום שעברו שעריהם מותרים אוטונומית. אין force-push, שינוי חתימה או הצגת Debug/סימולטור כהפצה. מפתח פרטי, Apple Team/ASC, אישור תנאים/זכויות ומכשיר פיזי אינם מומצאים; הוראות ב־EXTERNAL_ACTIONS. ארטיפקטים זמניים, אך SHA/run/commit וסיכומים קבועים נמצאים ב־qa.
