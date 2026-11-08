# בדיקות, התקנה ודיווח — גרסת פיתוח 1.3.9

ההפצה הציבורית החתומה האחרונה נשארת **1.3.5-beta**. קובץ `DEBUG_NOT_FOR_UPGRADE.apk` מיועד למכשיר בדיקה נקי בלבד ואינו משדרג את ההפצה הציבורית. אין להסיר את האפליקציה הציבורית כדי לעקוף אי־התאמת חתימה: הסרה עלולה למחוק נתונים. קובץ `UNSIGNED_NOT_INSTALLABLE.apk` הוא מועמד לחתימה, ואינו קובץ להתקנה.

Android: מזהה החבילה נשאר `il.org.lawreader.consumer`, מינימום Android 8 / API 26, יעד API 36. במכשיר ישן נדרש גם Android System WebView או Chrome התומך בממשק המודרני. CI מתקין עותק של ההפצה הישנה שנחתם מחדש **לבדיקה בלבד**, שומר בו נושא וקישור, מפעיל מחדש ומתקין מעליו את החדש באותה זהות בדיקה. זה מאמת מעבר נתונים ומספרי גרסאות, ואינו מאמת שדרוג חתום במפתח ההפצה המקורי.

iOS: מזהה המקור `io.github.sargon17green.consumerlawreader`, iOS 16 ומעלה, iPhone ו־iPad. ארטיפקט סימולטור אינו IPA ואינו ניתן להתקנה רגילה באייפון. אין קישור TestFlight עד לחתימה בחשבון מורשה, העלאה וקליטה ב־App Store Connect. מסלול הבנייה מפורט ב־[IOS_TESTFLIGHT_HE.md](../IOS_TESTFLIGHT_HE.md).

| סביבה אוטומטית | תרחישים קבועים | ראיות |
|---|---|---|
| Python 3.12 / Node 22 | גיבוב מקור, DOM, גרסאות, קישורים, פורמט/rollback, 500 מקרי Unicode, חוסן אריזה | לוג job `source-and-browser` |
| Chromium / Playwright | מסמך מלא, חיפוש→סעיף→חזרה, Back, העדפות, הזרקת iframe, רצף ניווט, רוחבים 320/430/768/1180 | `shared-reader-browser-evidence` |
| axe-core 4.11 | קריאה, חיפוש, תוכן עניינים, הגדרות, ניגודיות כהה/כחולה וגופן 28 בארבעת הרוחבים | JSON נגישות באותו ארטיפקט |
| Android Emulator API 26/31/36 | התקנה ושדרוג, תהליך חדש, תאריך מקוון, קישוריות מנותקת, DOM, Back, סיבוב, Clipboard, Word, SAF | `android-emulator-api-*`, לוגים וצילום אמולטור |
| iPhone/iPad Simulator iOS 26.2, iPhone iOS 18.5 | WKWebView אמיתי, מדיניות משאבים/גשר, חיפוש, Back, קובץ גיבוי, שיתוף, סיבוב והפעלה מחדש | `ios-*-evidence`, קובצי xcresult וצילומי הסימולטור |

קיומה של בדיקה בטבלה אינו הכרזת PASS. **רק run שהסתיים ו־job שהסתיים בהצלחה** הם ראיה לקבלת הגרסה. ריצות, commit ותוצאות מפורטים בדוח ההנדסי. ארטיפקטים ב־Actions מוגבלים בזמן; ראיות הקבלה המרכזיות נשמרות גם בתיקיית הדוח.

פיתוח מתבצע ב־Work וב־CI; אין צורך להריץ חבילת כלים במחשב Windows של המשתמש. לבעלי סביבת פיתוח קיימת, פקודות הבסיס הן:

```bash
python -m pip install -r requirements-qa.txt
python scripts/build_web.py
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/mobile_core_qa.js
node tests/pastafari_widget_qa.js
python scripts/verify_release.py
```

דיווח ב־[GitHub Issues](https://github.com/Sargon17-Green/consumer-law-reader/issues/new). אפשר להעתיק תבנית מתוך ״עוד״ → ״משוב על גרסת הבטא״. אין שליחה אוטומטית.

```text
גרסה ומספר build:
מכשיר / דגם:
מערכת וגרסה:
גרסת Android System WebView, אם רלוונטי:
סעיף / תקנה / קישור:
פעולות מדויקות לשחזור:
מה קרה בפועל:
מה צפיתי שיקרה:
האם התקלה חוזרת אחרי פתיחה מחדש:
מצב רשת, כיוון מסך וגודל גופן:
```

יש להסיר מידע אישי מצילומי מסך. אין לצרף גיבוי אישי, מפתחות או סיסמאות ל־Issue ציבורי. בדיקות TalkBack/VoiceOver אנושיות, מכשירים פיזיים, הדפסה פיזית ופתיחת מסמך בתוכנת Word עצמה אינן נחשבות שבוצעו מכוח בדיקות ה־CI.
