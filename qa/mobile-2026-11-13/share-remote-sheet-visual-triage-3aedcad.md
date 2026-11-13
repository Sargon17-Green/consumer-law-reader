# iOS — אבחון מראה חלוניות מערכת בריצה 3aedcad

מועד 13.11.2026. מקור אמת: ראש PR #11 במאגר `Sargon17-Green/consumer-law-reader`, ו־GitHub Actions completed artifacts / xcresult מה־SHA `3aedcadcdd64c8415c28a9edababa7b738bd7d53` (tree `9b2e880c0f09028ccd5addd3eb8e39274a091610`).

## סיכום קבלה מאומת

- [Linux/Web/Android run 43382168208](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43382168208): **9/9 completed/success**.
- [iOS run 43382168200](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43382168200): **3/6 completed/success**. עברו iPhone16, iPhone18.5, iPhone26.2 עם accessibility XXXL. נכשלו iPhone26.2 רגיל, iPad18.5, iPad26.2. כל הפרופילים הגיעו ל־XCUITest לאחר preflight install/launch ממשי (כשל FrontBoard מהמחזור הקודם לא חזר).
- אין 15/15 PASS; PR#11 חייב להישאר draft, ללא מיזוג או הפצת iOS לא חתומה.

## שלוש תקלות שונות, עם צילומים והיררכיות מתוך הצרופות המקוריות

1. **iPhone26.2**, job `131742215202`, artifact `14018555680`. מבחן `testNativeShareAfterFileImporterWithoutPrint` נכשל ב־`ReaderUITests.swift:145`: `Cancel` של Files אינו `isHittable` לאחר 60 שניות. התצלום `08DB5426-FED5-4D6F-9D10-AE127CCF4254.png` מראה חלון `fileImporter` לבן, ללא רכיבי פעולה. `B8CADB0C-71FA-4A9F-8445-3449FF4EA3A7.txt` מכיל native-share/menu מתחת לחלון, אך *אין Cancel*. לעומת זאת cold, print→share ומבחן הרצף המלא **PASS** באותו job. מצב החלון הלבן אינו מוסבר על ידי selector בלבד; דרוש בירור UIKit/DocumentManager.
2. **iPad18.5**, job `131742215203`, artifact `14020360484`. מבחן cold share נכשל ב־`ReaderUITests.swift:197`. צילום `ABE2A074-41DA-4C19-B06B-7BAAF399227E.png` מראה את הקורא עם רקע מעומעם ובלי פעולות השיתוף; קובץ `ED1A172B-E717-45B7-8459-128C3C8E049B.txt` כולל `ActivityListView/ShareSheet.RemoteContainerView`, אך **ללא header.closeButton**; שני צילומי cold share מציגים מצב לא מאוכלס. לעומת זאת Files→share, print→share והרצף המלא **PASS**.
3. **iPad26.2**, job `131742215757`, artifact `14018601370`. מבחן full נכשל ב־`ReaderUITests.swift:344`: אחרי Print→Files→Cancel נעשתה הקשה אמיתית על `native-share`; השאילתה ל־`ActivityListView` דרשה 8 שניות בלבד. הלוג מעיד כי השאילתה היחידה הראשונה ל־AX ארכה כ־7.2 שניות; `3954E063-4D8D-4D27-A8DE-60B6B62E0E96.txt` מציג חלון SwiftUI שני, אך לא `ActivityListView` ב־snapshot. cold, print→share, Files→share **PASS**; גם חלון iPad/resizing אינו נכשל באותה ריצה. קיומו של חלון SwiftUI נוסף אינו מוכיח ש־ShareSheet הופיע כראוי.
   
## השינוי המדוד במחזור הבא

- **יישור timeout ב־XCTest בלבד:** במבחן הרציף `testSearchNavigationSharingRotationAndRelaunch`, המתנת `ActivityListView` הוגדלה מ־8 ל־30 שניות, בדיוק כמבחני ה־share העצמאיים שכבר הוכחו. אין שינוי בדרישת `Close.isHittable`, לחיצה אמיתית, היעלמות חלונית, רוטציה, relaunch או שאר בדיקות UI.
- כאשר `ActivityListView` עדיין חסר אחרי 30 שניות, המבחן שומר **צילום מסך וגם עץ AX מקומי** לפני הכשל. בכך אי־הופעה של הממשק אינה מסווגת בטעות כ־PASS.
- **לא** שינינו את `ActivitySheet`, `.fileImporter`, `UIActivityViewController` או תכני החוק על סמך שלוש תופעות מחלונות מערכת שאינן מצביעות על גורם שורש זהה. שני המקרים של משטח לבן/remote blank עדיין פתוחים לאבחון, ואסור "לתקן" אותם על ידי הסרת assert.

## שער ההמשך

יש לבדוק את שתי הריצות החדשות על אותו HEAD לפני כל commit נוסף. לכל אחת מ־9/6 עבודות: `completed`, `conclusion`, ובכל FAIL גם לוגים ו־xcresult. להבחין בין תיקון של iPad26 (8→30 שניות) לבין כשלי iPhone26 Files ו־iPad18 cold. לדרוש 15/15 `completed/success` על אותו SHA/tree בטרם מיזוג, וכן אימות שמירת המשפט ודרישות חתימה לשחרור. פרויקט/ענף/PR יחיד, ללא הרצת CI כפולה.
