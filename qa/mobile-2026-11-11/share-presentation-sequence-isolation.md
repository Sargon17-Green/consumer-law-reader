# בידוד כשל שיתוף: קריאה חדשה לעומת רצף לאחר Print/Files

11.11.2026. מקור: ריצות GitHub Actions וארטיפקטי `xcresult` מקוריים; לא תמלילי שיחה.

## תוצאת מועמד 4ffbed4

- HEAD: `4ffbed4a1e177d6a444e157ee00ec14e05484b25`, tree `1b8f71a291d7a96745030e1aef8e4277635ba17b`.
- [Linux/Web/Android 43072821712](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43072821712): `completed/success`, 9/9.
- [iOS 43072821715](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43072821715): `completed/failure`, 3/6. הצלחות: iPad26.2, iPhone26.2 accessibility XXXL, iPhone18.5. כשל: iPhone26.2, iPhone16.0, iPad18.5.
- שלושת ה־FAIL הם `ReaderUITests.swift:163` אחרי `ActivityListView`, אין Close נגיש מסוג `isHittable` ב־15 שניות. אין להניח שכל כשל הוא אותו גורם.
- בארטיפקט iPad18.5 `13883260429` מופיע בעץ AX `NavigationBar UIActivityContentView` עם `header.closeButton` ש־frame שלו `{{632,215},{43,44}}`, ובצילום נראית חלונית פעולות. אף על פי כן XCTest לא ראה אותו לחיץ בחלון הבדיקה — ייתכנו תזמון או בדיקת hittability. זה **אינו** הוכחת כשל UI לצרכן.
- בארטיפקט iPhone26.2 `13881921360` מופיע `ActivityListView / ShareSheet.RemoteContainerView` ללא תוכן פעולות/Close בתמונת הכשל. זה שונה מה־iPad. אין להמציא סיבת שורש מרכיב זה.
- הפרופילים הקודמים עברו/נכשלו באופן משתנה בין קומיטים, כך שאין לייחס ארבעה FAIL רצופים רק ל־selector. שינוי מוצר מוצדק רק לאחר בידוד רצף.

## ניסוי ייצור מחייב, ללא הסתעפות

מתווסף קבוע מבחן XCUITest בשם `testNativeShareDirectlyAfterColdLaunch` במחלקה `ReaderUITests`. הוא:
1. מפעיל יישום מותקן חדש, מחכה ל־menu/share מוכנים (ולא מסתמך על עץ טעינה).
2. מפעיל `native-share` **לפני** Print, Files, מקלדת, סיבוב או חיפוש.
3. מחייב `ActivityListView`, כפתור Close ממשי עם `isHittable`, לחיצה עליו, היעלמות החלונית והפעלת פקדי reader. שומר צילום מסך והיררכיה מלאה אם אין Close.
4. אינו מחליף, מקצר או מדלג על `testSearchNavigationSharingRotationAndRelaunch`, שבודק את *אותה* פעולה אחרי שרשרת ארוכה של ממשקי מערכת.

## הכרעה חד־מסלולית לפי תוצאות completed

- **Fresh PASS / Sequential FAIL**: בעיית תזמון/מעברי presentation אחרי הפעולות הקודמות; להתמקד בפעולות Print/Files וחזרה למצב UIKit נקי. לא לשנות או להחליש מבחן שיתוף.
- **Fresh FAIL / Sequential FAIL**: לבחון הצגת UIActivityViewController מלכתחילה, בדגש iPad popover מול iPhone modal; לעיין בראיות Apple, לשקול שינוי מוצר מבוקר במקום selector.
- **Fresh FAIL / Sequential PASS**: לחפש תלות בטעינה ראשונית/מצב מוצג; לא להסיק פתרון מקומי.
- **שניהם PASS בכל ששת הפרופילים, וכל9 Linux/Web/Android PASS על אותו SHA/tree**: נדרש עדיין אימות תנאי המיזוג, שמירת חתימות מקור והגנות; רק אז ניתן להסיר draft ולמזג.

תוצאות `queued`/`in_progress` אינן PASS ולא חסם, ואין לפתוח ריצה נוספת או לדחוף קומיטים תוך כדי. אין שינוי בחוק `original/Consumer_Protection_Law.html`, בהפצה הציבורית, חתימות או ב־`latest.apk`. תוצאות חדשניות יתועדו באותו מאגר וב־PR #11 בלבד.
