# חוק הגנת הצרכן, התשמ"א–1981 — אפליקציית iOS מקורית (פיתוח)

## מה קיים כעת

- קוד אפליקציית **SwiftUI** לאייפון ולאייפד תחת `ios/ConsumerLawReader`. זה יישום iOS אמיתי, לא קיצור דרך למסך הבית.
- נוסח החוק וחקיקת המשנה נארזים בתוך היישום מתוך אותו קובץ מקור מקומי, באמצעות `scripts/build_web.py`. הקריאה והחיפוש אינם מחייבים חיבור רשת.
- מעטפת `WKWebView` מציגה את הטקסט המקומי; משאבי רשת חיצוניים נחסמים למעט שלושת מקורות ה־JSON המדויקים של רכיב התאריך. סקריפטים ומסגרות חיצוניים נשארים חסומים. פתיחת קישורי HTTP/HTTPS ביוזמת המשתמש מעבירה ל-Safari.
- כלי iOS: שיתוף קישור לסעיף, הדפסה / שמירה ל-PDF דרך מערכת ההדפסה, יצוא הגדרות מקומיות לקובץ JSON ושחזור באמצעות בורר הקבצים עם אישור לפני החלתן.
- תכונות קריאה, חיפוש וניווט קיימות נלקחות מממשק המקור המשותף ל-Android ול-Web.

**אין עדיין הפצה ב-TestFlight או IPA חתום.** קוד iOS אינו מעיד שקיים חשבון Apple Developer, חתימה או אישור Apple.

## בדיקה אוטומטית

הפעולה [Build native iOS app (unsigned simulator)](https://github.com/Sargon17-Green/consumer-law-reader/actions/workflows/ios-ci.yml) רצה על macOS ומייצרת אפליקציית סימולטור לא חתומה, לאחר אימות מקור החוק, התוכן המוטמע ובדיקות התקינות. נבחר Xcode 26.3; XCTest ו־XCUITest מפעילים WKWebView וממשק Native ב־iPhone/iPad iOS26.2/18.5 וב־iPhone iOS16.0, ובפרופילiPhone26.2 נוסף בגודל נגישות XXXL. יש להבחין בין הגדרת המטריצה לתוצאות completed המתועדות. אין צורך להריץ ידנית בדיקות CI. דוחות xcresult וצילומים נשמרים ב־Actions, ורק ריצות completed/success הן ראיות PASS. התהליך מכין גם ארכיון מכשיר לא חתום לאחר הצלחת הבדיקות. הצלחה ב-CI אינה תחליף להרצה על אייפון אמיתי.

## בנייה והתקנה במחשב Mac

דרישות: macOS עם Xcode 26.3 או SDK מתאים לדרישות Apple העדכניות, XcodeGen2.46.0 (התקנה מקובעת בגיבוב ב־`.github/workflows/ios-ci.yml`), Python 3 וחיבור למאגר הפרויקט.

```bash
git clone https://github.com/Sargon17-Green/consumer-law-reader.git
cd consumer-law-reader
python3 -m pip install -r requirements-qa.txt
python3 scripts/build_web.py
python3 scripts/verify_release.py
bash ios/scripts/prepare_assets.sh
xcodegen generate --spec ios/project.yml --project ios
open ios/ConsumerLawReader.xcodeproj
```

בחר בתוכנית **ConsumerLawReader**, מכשיר iPhone Simulator, והפעל. התקנת גרסת בדיקה על iPhone פיזי דורשת שיוך Xcode לחשבון פיתוח וחתימה תקינה; הוסף את חשבון Apple ב-Xcode → Settings → Accounts ובחר Team בפרויקט. אם מזהה החבילה שבדוגמה אינו פנוי בחשבונך, יש להתאים אותו לפני רישום ב-App Store Connect.

## שלבי יצירת TestFlight

1. **חברות פעילה ב-Apple Developer Program.** נדרשים גם הרשאות ל-App Store Connect ומחשב Mac עם Xcode לצורך ארכיון וחתימה, או מערכת CI שמוגדרת לכך באישור הבעלים.
2. באפליקציות ב-[App Store Connect](https://appstoreconnect.apple.com/) צור רשומת אפליקציה ב-iOS, עם שם הפרויקט, מזהה Bundle ID ייחודי ושאר הפרטים הנדרשים. מזהה ברירת המחדל בתבנית הוא `io.github.sargon17green.consumerlawreader`; הוא אינו רישום קיים ולא אומת כבעלות.
3. במחשב Mac, לאחר הגדרת החשבון ב-Xcode, בנה ארכיון חתום:
   ```bash
   export APPLE_TEAM_ID='YOUR_TEAM_ID'
   export IOS_BUNDLE_ID='YOUR_REGISTERED_BUNDLE_ID'
   bash ios/scripts/archive_for_testflight.sh
   ```
4. ב-Xcode: **Window → Organizer → Archives → Distribute App → TestFlight & App Store → Upload**.
5. רק לאחר קליטת הגרסה ב-App Store Connect ניתן להפעיל בדיקות TestFlight. בודקים חיצוניים עשויים לחייב Beta App Review. רק אז אפשר לשתף קישור הזמנה ל-TestFlight.

הפרויקט אינו אוסף או שומר מפתחות Apple או סיסמאות במאגר GitHub. אין להעלות אותם לקוד או ל-Issue.

## גבולות ושאלות איכות לפני ההפצה

- לא נבדק עדיין שהאפליקציה עובדת על iPhone פיזי. הכיסוי האוטומטי המפורט ב־docs/MOBILE_TESTING_HE.md אינו מחליף בדיקת VoiceOver ומכשיר פיזי. אין צורך להריץ ידנית בדיקות שכבר מתבצעות ב־CI.
- Apple בוחנת **פונקציונליות מינימלית**; מעטפת של אתר בלבד עלולה להידחות (App Review Guideline 4.2). נוספו יכולות iOS, אך אין הבטחה שהיישום יאושר.
- לצורך App Store Connect נדרשים גם פרטי פרטיות, גיל דירוג, תיאור, תמונות מסך, סמל ומידע למעריכי היישום. ייתכן צורך באישורים נוספים.
- העורך והמפרסם הוא **סרגון 17 גרין כאדם פרטי**, לא רשות ממשלתית. תאריך נכונות נוסח החוק נשאב מקובץ `metadata/editorial_status.json` ואינו מתקדם אוטומטית.
- תוכן אתר המקור שכולל צדדים שלישיים עשוי להצריך בדיקת רישיונות נפרדת. אין להתייחס לחתימה או להרצת CI כאישור לזכויות השימוש.

## אתרי Apple הרשמיים

- [הפצת בטא באמצעות TestFlight](https://help.apple.com/xcode/mac/current/en.lproj/dev2539d985f.html)
- [העלאת אפליקציה ל-App Store Connect](https://help.apple.com/xcode/mac/current/en.lproj/dev442d7f2ca.html)
- [כללי בדיקת אפליקציות](https://developer.apple.com/app-store/review/guidelines/)
