# המשך רציף: Ubuntu runner וה־Files picker — 12.11.2026

**מסלול יחיד:** `Sargon17-Green/consumer-law-reader` → PR #11 → `fix/pastafari-date-android-20261028`. אין ליצור ענף/PR מקביל. מסמך זה מבוסס על GitHub Actions `completed`, לוגים וצילומי `xcresult` בפועל, ולא על הנחות משיחה.

## ראש קודם, מצב מוכח

- Source/tree שנבדק: commit `78eeab9b87fe6b0bd5ec96af176009385291cccd`, tree `65265f8b2141a963b68e34abba8f9860eadb62d6`.
- [Linux/Web/Android run 43166949957](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43166949957): `completed/failure`. **4/9 PASS** (בניית Android ואמולטורים API26/31/36), **5/9 FAIL** (source/browser + ארבע בדיקות דפדפן). כל חמשת הכשלים היו לפני בדיקות המוצר, בשלב התקנת browser: `ERROR: Playwright does not support chromium on ubuntu26.04-x64`. GitHub `ubuntu-latest` פתר בפועל למערכת 26.04. לא הוכחה רגרסיית Web/Android. אין לסמן 9/9 PASS.
- [iOS run 43166950060](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43166950060): `completed/failure`, **4/6 PASS**: iPhone 26.2, iPhone 16.0, iPad 26.2, iPhone 26.2 XXXL. **FAIL**: iPhone 18.5 job `131010918411` ו־iPad 18.5 job `131010918717`. בשניהם הבדיקה `testNativeShareDirectlyAfterColdLaunch` עברה, ו־`testSearchNavigationSharingRotationAndRelaunch` נכשלה בשורה 205, `Files picker must dismiss before the next system presentation` — עוד לפני ניסיון פתיחת השיתוף.

## ראיות צילום מסך מקוריות ל־iOS 18.5

- [ארטיפקט ריצה 43166950060](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43166950060), iPhone 18.5 artifact `13922181666`, `iPhone-ios-18.5-attachments/DB6B6148-39A5-4FCC-90A3-3C84B05D8159.png`.
- באותה ריצה, iPad 18.5 artifact `13922625312`, `iPad-ios-18.5-attachments/817D1BD1-EB6E-4FD6-BC6E-7D17D9DC9F87.png`.
- בשני הצילומים המסומנים `Files picker lifecycle after Cancel before share` **בורר הקבצים אינו גלוי**. במקום זאת מוצגים ממשק הקורא המלא והכותרת/פעולות native. בלוגים לחיצת `Cancel` הממשית בוצעה לפני צילום הכשל; אין הוכחה שמבחינה חזותית הבורר נשאר פתוח.
- תנאי QA הישן דרש `!cancel.exists && !filePicker.exists`. רכיבי נגישות מרוחקים יכולים להישאר קיימים בעץ גם אחרי סגירת חלון. הכשל יכול לנבוע מסמני קיום מיושנים או מ־`menu.isHittable`; אין מידע מי מהם גרם ל־timeout. **לא נקבע גורם שורש פנימי של UIKit.**

## תיקון מוגבל ותנאי קבלה למחזור הבא

1. קיבוע כל ארבעת `runs-on` ב־`.github/workflows/ci.yml` מ־`ubuntu-latest` ל־`ubuntu-24.04`; אין עדכון גרסת Playwright, דילוג על בדיקות או שינוי קוד מוצר.
2. מבחן ההחזרה מ־Files ישתמש ב־`!cancel.isHittable && !filePicker.isHittable` ובמקביל **יחייב** `menu` ו־`native-share` שהם `exists/isEnabled/isHittable`. כך בורר גלוי וחוסם אינו מתקבל, ואילו רכיב נגישות לא פעיל שנותר בעץ אינו גורם לכשל שווא.
3. אם ה־predicate נכשל גם כך, לצרף צילום מסך ו־AX tree של כל היישום, לא להחליש את ההוכחה או להעלות timeout באופן עיוור.
4. עדיין חייבים לעבור בפועל את כל בדיקת השיתוף הנפרדת והמשולבת, כולל `ActivityListView`, `Close.isHittable`, tap והיעלמות; לא הוסר שום מבחן, ולא שונו SwiftUI/UIKit, נוסח החוק, ההפצה או זהות החתימה.

## השלמה והעברת המשימה

לאחר שייווצר commit חדש, חובה לבדוק `HEAD` ולתעד מזהי **שתי ריצות CI** שנפתחו עליו. בזמן `queued/in_progress` אין להזיז את ראש PR #11, לבצע dispatch כפול או להסיק PASS. לאחר `completed`, לקרוא כל אחת מ־9+6 העבודות; רק 15/15 PASS **על אותו SHA/tree** מאפשר בדיקת תנאי מיזוג, ולכל כשל אחר צריך ראיות חדשות מן הריצה המסוימת. חתימות Android/iOS ממשיכות להיות תלויות בהרשאות/מפתחות המקוריים ומפורטות ב־`EXTERNAL_ACTIONS.md`.
