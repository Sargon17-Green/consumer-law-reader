# בידוד הצגת שיתוף וקבצים — מחזור 2cd630a

תאריך: 12.11.2026. המסמך הוא מקור להמשך עבודה אחרי מחזור QA שהושלם. אין להסיק ממנו עמידה מלאה בתנאי הקבלה.

## ראיות מאומתות

- מועמד ראש `2cd630a143860a50aad58748b131ab116f49a5b1`, tree `6d118dfb7566abb917b1e34b1a398a98723f2e23`.
- [מקור/Web/Android 43084085468](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43084085468): `completed/success`, **9/9** עבודות.
- [מטריצת iOS 43084085576](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43084085576): `completed/failure`, **2/6** עבודות (XXXL iPhone26.2 ו־iPhone18.5) עברו, ארבע נכשלו. 6/6 נבנו והגיעו למבחני iOS האמיתיים.

| פרופיל | שיתוף מפתיחה נקייה | מבחן רציף | job |
|---|---|---|---|
| iPhone 26.2 | PASS, Close זוהה ונלחץ | FAIL: Share Close `ReaderUITests.swift:203` | 130743822849 |
| iPhone 26.2 XXXL | PASS | PASS | 130743822433 |
| iPhone 18.5 | PASS | PASS | 130743822764 |
| iPhone 16.0 | PASS, Close label ללא identifier | FAIL: Share Close `ReaderUITests.swift:203` | 130743822817 |
| iPad 26.2 | PASS | FAIL: בורר Files פתוח אך Cancel לא אותר ב־`ReaderUITests.swift:175` | 130743822082 |
| iPad 18.5 | FAIL: Share Close ב־`ReaderUITests.swift:72` | FAIL: Share Close ב־`ReaderUITests.swift:203` | 130743822543 |

## בדיקת ארטיפקטי xcresult מקוד המקור

ארטיפקטים הושגו מ־GitHub Actions, לא מהודעות שיחה:
- iPhone26.2 artifact `13887245616`: מצב cold launch מציג UI שיתוף תקין; במבחן הרציף, היררכיית AX בסוף הכשל **כן כוללת** `UIActivityContentView` עם `header.closeButton` בגודל 36×36 ואת `actionGroupCell Copy`. למרות זאת polling `isHittable` במשך 15 שניות נכשל; לא הוכחה בעיית מוצר של כפתור חסר.
- iPad18.5 artifact `13887278134`: במבחן ה־cold launch מיכל `ShareSheet.RemoteContainerView` קיים אך ללא כפתור/תוכן פעולות גם בתצלום הכשל; במבחן הרציף ה־UI **כבר מאוכלס** עם `header.closeButton` בגודל 43×44 אך השאילתה לא מצאה כפתור לחיץ בזמן 15 שניות. שני מצבי כשל שונים, וגורם השורש לא הוכח.
- iPad26.2 artifact `13888055771`: picker `Browse View (Picker)` אכן מוצג; ההיררכיה מכילה `DOCSidebarView` ומתחתיו `Button Cancel` בגודל 46.5×36, ב־PID נפרד, אך שאילתת `app.buttons.matching(label IN ...).firstMatch` נכשלה במשך 60 שניות. זהו כשל איתור QA בממשק מערכת, לא הוכחה שבורר הקבצים לא נפתח.

## ההשערות המוגבלות במחזור הבא

ללא שינוי SwiftUI/UIKit, מקור החוק או זהות חתימה, בדיקת UI מורחבת כך:
1. ב־iPad Files picker מקדימים שאילתת `app.navigationBars["DOCSidebarView"].buttons["Cancel"]` לפני fallback הגלובלי. נדרש כפתור ממשי `isHittable`; כשל שומר צילום ו־AX.
2. לאחר cancel מחכים להיעלמות Cancel, להיעלמות `Browse View (Picker)` ולהפיכת `native-menu` ל־`isHittable`; לא מניחים שאפשר לפתוח share על סמך עצם קיומו של menu מתחת למודאל.
3. בתוך השיתוף המבחן הרציף נותן 45 שניות, בדיוק כמו מבחן cold launch, לבירור Remote ShareSheet AX. הוא **אינו מרפה** מתנאי `ActivityListView`, `isHittable`, לחיצה על Close והיעלמות חלון השיתוף. 15 שניות אפשרו רק 2–3 קריאות AX איטיות בחלק מהריצות.
4. אם iPad18.5 cold share עדיין אינו מאוכלס גם אחרי 45 שניות: זו אינה תקלה שתיקון selector/timeout פותר; בדוק presentation architecture ב־SwiftUI/UIViewControllerRepresentable ואת כללי `popoverPresentationController` הרשמיים של Apple לפני שינוי מוצר מבוקר. מקורות: https://developer.apple.com/documentation/swiftui/modal-presentations ; https://developer.apple.com/documentation/uikit/uipopoverpresentationcontroller .
5. כאשר הריצות החדשות יסתיימו, לתעד בפירוט את **שני** מבחני שיתוף בכל אחד מששת פרופילי iOS ואת 9 עבודות Linux/Android על אותו SHA.

## כלל ההמשך המחייב

הריצה הבאה על ראש PR #11 חייבת להסתיים לפני כל commit נוסף. לא פותחים ענף או PR חלופי; לא ממזגים בלי 9/9+6/6 PASS completed על אותו SHA/tree, בלי אימות תנאי release; לא משנים HTML משפטי, חותמים במפתח חדש או מחליפים `latest.apk`. אם הריצה נכשלת, כשל ספציפי מהארטיפקט החדש מגדיר את התיקון הבא; לא משחזרים טענות ישנות או עוברים לנושא צדדי.
