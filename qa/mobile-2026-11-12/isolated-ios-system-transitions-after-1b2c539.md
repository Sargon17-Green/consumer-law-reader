# תוכנית בידוד מעבר בין מערכות iOS — ממצאי 1b2c539

מועד אבחון: 12.11.2026. PR #11, ענף `fix/pastafari-date-android-20261028`. מקור אמת: ריצות completed ב־GitHub, לוגים לפי עבודת CI ואחריהם קובצי XCTest. אין להסתמך על תיאור שיחה.

## שער 1b2c539: תוצאות

- SHA `1b2c539e47d911091379f34605fbf19edb8a66e8`, tree `7791b6d73113934783922f516e17f28e7f79ce54`.
- [Source/Web/Android 43226919725](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43226919725): **9/9 completed/success**. קיבוע runner `ubuntu-24.04` תיקן כשל התקנת Playwright 1.57.0 ב־Ubuntu 26.04; source, ארבעה רוחבי Web, Android debug ושלושה אמולטורים עברו.
- [iOS 43226919738](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43226919738): **0/6 jobs success**, 5 failure ואחד cancelled. כל ששת הפרופילים הגיעו לבדיקות XCTest; לא התקבל מועמד. תוצאות קודמות על SHA שונה אינן משלימות את הקבלה.

| פרופיל | שיתוף בפתיחה נקייה | כשל רציף ומיקומו |
|---|---|---|
| iPhone26.2 | FAIL; Share Close אינו hittable (שורה72) | Files Cancel אינו hittable (שורה191) |
| iPhone18.5 | FAIL; Share Close אינו hittable (שורה72) | אחרי Cancel אין הוכחת חלון Files סגור ו־Share לחיץ (שורה213) |
| iPhone16.0 | PASS | אחרי Cancel לא ניתן להוכיח שה־Share לחיץ (שורה213) |
| iPad18.5 | PASS | אחרי Cancel לא ניתן להוכיח שה־Share לחיץ (שורה213) |
| iPad26.2 | PASS | print Close לא הגיע ל־isHittable (שורה156); בנוסף בדיקת חלון iPad נכשלה בסגירת Menu (שורה127) |
| iPhone26.2 XXXL | FAIL; לא הופיע ActivityListView בפתיחה נקייה (שורה55) | מבחן רציף PASS; בדיקת עבודת CI נכשלה בגלל מבחן cold |

**המשמעות:** כשלי presentation ו־AX משתנים בין ריצות; 15/15 PASS טרם הושג. אין ראיה שסקריפט שונה במקור החוק הוא הסיבה; אין גם הוכחה שמדובר אך ורק בכשלי XCTest, ולכן אסור להחליש דרישות UI ללא בדיקה.

## השערה לבדיקה במקום תיקון עיוור

קוד המוצר משתמש ב־SwiftUI `.sheet(item:$reader.sharing)` שעוטף `UIActivityViewController` באמצעות `UIViewControllerRepresentable`, לצד `.fileImporter` ו־`UIPrintInteractionController.shared`. לפי [תיעוד Apple של UIActivityViewController](https://developer.apple.com/documentation/uikit/uiactivityviewcontroller/) ההצגה ב־iPad נעשית ב־popover, וב־iPhone מודאלית. מצבי print, Files ו־share עשויים להפריע זה לזה; **זה טרם הוכח** ואין לבצע refactor UIKit לפני בידוד.

בקומיט הבא נוסף **מכשיר אבחון שאינו משנה מוצר**: שני מבחני XCUITest חדשים, שמתווספים ואינם מחליפים את המבחנים הקיימים:
1. `testNativeShareAfterPrintWithoutFileImporter`: אפליקציה חדשה, Print system, לחיצה על Close הממשי ואימות היעלמות, ואז Share system ואימות Close/היעלמות. אין שימוש ב־Files או בחיפוש.
2. `testNativeShareAfterFileImporterWithoutPrint`: אפליקציה חדשה, פתיחת בורר Files וביטולו, אימות שאינו קולט קלט ושפקדי app לחיצים, ואז Share system. אין שימוש ב־Print או בחיפוש.
3. `verifyIsolatedNativeShare`: בדיקת ActivityListView, Close `isHittable`, לחיצה והיעלמות, עם קובצי AX וצילום מסך בכשל.

**דרישת החלטה לאחר completed:** להצליב, **בכל פרופיל בנפרד**, ארבעה מצבים: cold share, print→share, Files→share, full scenario. אם print→share FAIL בלי Files, מקור הבעיה לפני בורר; אם Files→share FAIL בלי print, להתמקד במחזור החיים של Files; אם שניהם PASS ורק full FAIL, לבודד אפקט סדר/חיפוש/IME; אם cold עצמו FAIL, לחקור presentation popover/modal. אין לשנות את מסלול ההפצה או להסתפק ב־hittability שהושג על ידי הסרת assert.

## מפתח המשך מחייב

המתן לשתי ריצות חדשות על **אותו SHA**, אל תדחוף קומיטים בזמן queued/in_progress, אל תפעיל CI כפול. קרא כל job, ודא 9/9+6/6 completed/success לפני מיזוג, שמור ראיות ארטיפקטים. המשך ב־PR #11 ובענף היחיד. אין שינוי ב־`original/Consumer_Protection_Law.html`, תעודת Android המקורית, `downloads/latest.apk`, App Store signatures או פרסום גרסה חדשה.
