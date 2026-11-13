# מחזור 9995a85e — מגבלת זמן ואימות התקנת סימולטור

13.11.2026; מסלול יחיד: `Sargon17-Green/consumer-law-reader` → PR #11 → `fix/pastafari-date-android-20261028`. מקור הנתונים: ריצות GitHub Actions completed, per-job logs.

## ממצאים קונקרטיים

על head `9995a85ee94d3450531bdf2a5c1ad499bea9bc70`, tree `a54caa18172639587938677d14fbe3dae16c13c6`:
- [Source/Web/Android 43316834311](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43316834311) — **9/9 success**.
- [iOS 43316834229](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43316834229) — **1/6 success**: iPad iOS18.5 PASS, iPad iOS26.2 FAIL, ארבע עבודות iPhone cancelled. תוצאה זו **לא** מספיקה למיזוג.
- iPad18.5 job `131526930856`: `TEST SUCCEEDED`, כלל ארבעה מבחני שיתוף (Files→Share, Print→Share, cold, full), יחד עם יתר מבחני UI. ראיה חיובית ממשית להתקנה, פתיחה וסגירת חלוניות.
- iPad26.2 job `131526930663`: `TEST FAILED` **ללא כשל XCTest בודד**; `FBSOpenApplicationErrorDomain Code=4 NotFound` על הבינארי `io.github.sargon17green.consumerlawreader` ועל `.uitests.xctrunner`. המערכת לא זיהתה את האפליקציה ואת runner ב־FrontBoard והבדיקות לא התחילו, על אף ש־build-for-testing הסתיים. אין להסיק שזהו באג ב־SwiftUI.
- iPhone26.2 job `131526930074`, XXXL job `131526930568` ו־iPhone16 job `131526930802`: לוגים מסתיימים `The operation was canceled` במהלך xcodebuild, ללא תוצאת XCTest סופית. ה־job הוגדר `timeout-minutes:30`, בעוד שחבילת XCTest כעת כוללת **שני מבחני UI עצמאיים נוספים**. ב־iPhone16 תועדו שלושת מבחני השיתוף העצמאיים PASS והמבחן המלא הגיע ל־`NATIVE_SHARE_CLOSE` בטרם ביטול.
- iPhone18.5 job `131526930610`: כל שלוש בדיקות השיתוף העצמאיות PASS, ובמבחן הרצף המלא `testSearchNavigationSharingRotationAndRelaunch` תועד במפורש `exceeded execution time allowance of 8 minutes` אחרי `NATIVE_SHARE_CLOSE`. גם ה־job הסתיים בביטול. זהו **חסם סף הרצה**, לא הוכחת כשל של פונקציית share, אך גם לא PASS.

## תיקון התשתית המתועד

1. `.github/workflows/ios-ci.yml`: `timeout-minutes` נעשה **55** כדי לתת זמן לכל ארבע בדיקות ה־UI הארוכות ומבחני windowing, במקום לבטל עבודה שמבצעת בדיקות תקינות סמוך ל־30 דקות. זהו שינוי תקציב ריצה על סמך מועדי הביטול, לא הרחבה שרירותית של תנאי קבלה.
2. מקסימום מבחן XCTest נפרד הוגדל מ־480 ל־720 שניות. ב־`ReaderUITests.swift` הוחל 720 רק על מבחן הרצף המלא `testSearchNavigationSharingRotationAndRelaunch`; מבחנים קצרים נשארו 480. **כל assertions המקוריים נשארים**.
3. בכל ששת פרופילי הסימולטור (ולא רק iOS16) נוסף preflight שמפעיל `simctl install`, מאמת `simctl get_app_container`, עושה `simctl launch` ואחר כך `terminate`. כך כשל NotFound יתועד לפני בדיקת XCTest, וניתן יהיה להפריד כשל התקנה ממימוש SwiftUI. בדיקת התקנת האפליקציה בסימולטור אינה חתימת IPA להפצה.
4. ה־CI החדש מופעל **פעם אחת** על ראש ענף קיים, בלי rerun כפול ובלי פתיחת PR/branch חלופיים. אין שינוי במשאב `original/Consumer_Protection_Law.html`, בהצפנה או בערוץ Android הציבורי.

## שער המשך

לאחר ששתי ריצות CI על SHA החדש **completed**: לקרוא כל אחת מ־9+6 העבודות, ארבעת מבחני share בכל פרופיל, התוצאות במבחן ההדפסה, החלונית, window resizing, והאם preflight הצליח. אם מתקבל failure — יש להסתמך על per-job logs/xcresult של אותו SHA בלבד. עד 15/15 completed/success על אותו tree ו־release guard אין למזג או לפרסם חבילה לא חתומה. אין להחליף משטר משפטי, אין לשנות את hash קובץ המקור. `PROJECT_HANDOFF.md` ו־PR #11 הם נקודת המשך מוסמכת.
