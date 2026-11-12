# המשך עבודה עצמאי — חוק הגנת הצרכן

עודכן ב־11.11.2026. הפרויקט הוא **Sargon17-Green/consumer-law-reader**: Android WebView, SwiftUI/WKWebView ל־iPhone/iPad וממשק Web/PWA משותף. המטרה היא לפרסם ערוץ בשל מוקדם ולהמשיך בפיתוח, בלי תלות בשיחה. אין לערבב עם אפליקציית לוח השנה.

## checkpoint 12.11.2026 — תנאי מעבר בין חלונות מערכת

תוצאות [43084085468](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43084085468) (**9/9 PASS**) ו־[43084085576](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43084085576) (**2/6 iOS PASS**) נבחנו בפועל על `2cd630a`. [דוח אבחון חדש לפי ארטיפקטים מקוריים](qa/mobile-2026-11-12/share-lifecycle-isolation-results.md) מפרט: iPad18.5 נכשל בשיתוף גם בפתיחה נקייה; iPhone16/iPhone26 עברו cold ונכשלו בשיתוף אחרי Print+Files; iPad26 הציג בפועל Files picker אך Cancel לא אותר על ידי השאילתה הגלובלית. המבחן הבא מקבע אותן דרישות close/hittability ודורש גם **סגירה אמיתית של בורר הקבצים** לפני פתיחת שיתוף, עם איתור ממוקד של `DOCSidebarView/Cancel`. לאחר יצירת commit חדש: **לא להזיז ראש PR #11 בזמן ריצות pending**, לא להסתמך על לוגים מ־SHA אחר ולא למזג עד 15/15 jobs completed/success.

## checkpoint חדש — אבחון השיתוף בשני רצפים, 11.11.2026

ריצות המועמד `4ffbed4a1e177d6a444e157ee00ec14e05484b25` הסתיימו: [9/9 source/Android PASS](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43072821712), [3/6 iOS PASS](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43072821715). כל שלושת הכשלים ב־iOS16, iPhone26.2 ו־iPad18.5 נובעים בשלב ה־UI מ־Close של ActivityListView שאינו `isHittable` בשאילתת XCTest. iPad26.2, iPhone26.2-XXXL ו־iPhone18.5 עברו. חלק מצילומי הכשל מציגים כפתור X וחלק מראים remote container לא מאוכלס. [דוח רצף הבדיקה החדש](qa/mobile-2026-11-11/share-presentation-sequence-isolation.md).

**שער הפעולה הבא:** ריצת CI על commit הבא, הכולל `testNativeShareDirectlyAfterColdLaunch` קבוע, לפני המבחן המלא. אין הסרת assertions מהמבחן המלא או שינוי UIKit לפני הכרעה. אם הבדיקה הקרה עוברת והבדיקה המשולבת נכשלת — לחקור מעבר אחרי print/Files. אם הקרה נכשלת — לחקור הצגת UIActivityViewController עצמה והתאמת מצבי popover/iPad על פי Apple. אחרי completed לאסוף xcresult, צילומי מסך ולוגים של כל פרופיל; אין לפרסם Native עד קבלה מלאה, ואין דחיפת קומיטים בזמן CI.

## checkpoint מחייב — לאחר completed על bfc2

[דו"ח המחזור האחרון ותור ההמשך](qa/mobile-2026-11-11/candidate-bfc2-failure-triage.md) מחליף כל טענת סטטוס ישנה: על `bfc2c828f0baba7c871de682f5fb3ee92a19466d`, [Linux/Web/Android 43060328220](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43060328220) עבר **9/9** ו־[iOS 43060328507](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43060328507) עבר **2/6 בלבד**. הוכנו תיקוני QA מדודים ל־preview/Close/share עם שמירת assertions וצילומי כשל. לאחר דחיפת הקומיט הכולל אותם: **לא משנים את ראש PR11 עד שתסתיימנה ריצותיו**. כשלי UIKit של סגירת print ב־iPhone26 והצגת share ב־iPad18.5 טרם נפתרו ואין לאשר את המועמד בלעדיהם.

## עדכון בדוק מ־11.11.2026 — קודם לקריאת שלבי ההמשך

[דו"ח קבלה מאוחדת שהושלמה](qa/mobile-2026-11-11/completed-acceptance-triage-20261111.md): על מועמד `5792b66`, תשעה מתוך תשעה jobs ב־Linux/Web/Android עברו ([run 42967750924](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750924)), אך שלושה מתוך ששת פרופילי iOS נכשלו ב־UI ([run 42967750794](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42967750794)). לפיכך **PR11 אינו כשיר עדיין למיזוג**. נדרש אבחון תצוגת PDF ב־XXXL, ביטול שחזור קובץ ב־iPhone18.5 וסגירת שיתוף ב־iPad18.5, ואז חזרה על מטריצה מאוחדת מלאה. הישג נפרד: [run 42968670868](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42968670868) אימת בפועל Save-to-Files מקומי ב־iPhone26.2: קובץ חדש 1,302,508 בתים, 136 עמודים ו־SHA-256 מתועד בדו"ח. זה לא PASS לכל הפלטפורמות ואינו חתימת הפצה.

## כניסה ומקורות האמת

[מצב המימוש](IMPLEMENTATION_STATUS.md), [63 הדרישות](PRODUCT_REQUIREMENTS.md), [קטלוג מובנה](docs/requirements.json), [BACKLOG](BACKLOG.md), [תקלות](KNOWN_ISSUES.md), [ארכיטקטורה](ARCHITECTURE.md), [בדיקות](TESTING.md), [הפצה](RELEASE_PROCESS.md), [היסטוריה](RELEASE_HISTORY.md), [החלטות](DECISIONS.md), [פעולות חיצוניות](EXTERNAL_ACTIONS.md), [דוח ומטריצת פלטפורמות](docs/MOBILE_ENGINEERING_2026-11-08_HE.md).

## מה זמין להתקנה

- [Web/PWA תיקון3](https://sargon17-green.github.io/consumer-law-reader/reader/) פורסם. אפשר להוסיף למסך הבית ב־Safari/Chrome; זהו יישום Web. מקורcca785ed8b1f3d4c96bf25c0eb50e77b04899566 ומטמון453decfde812ec9b. [75HTTP/SHA עברו מחדש](qa/mobile-2026-11-08/public-web-readonly-recheck.json), כולל alpha וה־APK הקודם.
- [Android v1.3.5-beta חתום](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk) הוא הקישור הציבורי הקבוע. הוא אינו מכיל את תיקוני1.3.9. המועמד החדש1.3.9-dev/code17 הוא Debug/unsigned בלבד; אין מפתח מקורי נגיש שאומת. [תחום הבדיקה](qa/mobile-2026-11-08/signing-availability-scope.json).
- iOS1.3.9/build17 נבנה בסימולטורים וב־device archive לא חתום. אין IPA חתום או TestFlight; אין להציג בניית סימולטור כהתקנה לאייפון רגיל.

## ענף, מצב ופעולה הבאה

1. לרענן את [PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11) ואת ראש הענף `fix/pastafari-date-android-20261028`. גוף ה־PR מציג SHA/tree ומזהי הריצות העדכניים. ענף `docs/mobile-release-evidence-20261110` שומר checkpoint של הידע; בסיס main המקורי016b3de352dabe97f51b34b78ff803965b6cd40d. אין hash עצמי של מסמך כמקור אמת.
2. **הצעד הבא: קבלה מאוחדת של9Linux/Android ו־6iOS על אותו tree.** מקור027 נכשל: Linux8/9 ו־iOS4/6. [הכשלים והניסויים](qa/mobile-2026-11-08/candidate-027-followup.json) נשמרו, כולל [תמונות מקוריות](qa/mobile-2026-11-08/screens/README.md). אין למזג027 על סמך הצלחות חלקיות.
3. [שלושת תיקוני ההמשך עברו ברכיבים](qa/mobile-2026-11-11/components-accepted.json): Android6d246d3/run42873698707 העביר31online/offline עם מקלדת, פוקוס ומחיקה/הקלדה Native; iOS200d5b7/run42874533215 העביר lifecycle ועוד8טעינות Native ב־18.5; iPadc853d3b/run42874102662 העביר את רצף ה־UI המלא עם עמוד print-preview ממשי ו־Close מוכן. הקוד והבדיקות הקבועים מאוחדים כעת; אין העתקת workflow מקוצר או DEBUG delegate מניסוי.
4. במטריצה הקבועה נבדקים iPhone26.2/18.5/16, iPad26.2/18.5 ו־iPhone26.2 בגודל מערכת accessibility XXXL. כל פרופיל מריץ9מבחני WK/policy ועוד UI; גם מקלדת תוכנה אמיתית, חלון iPad והפעלה מהסמל. XXXL כבר עבר ברכיב027; נדרשת קבלה למקור המאוחד. queued/in_progress אינםPASS או חסם; אין לפתוח ריצה זהה נוספת בגלל המתנה.
5. לאחר completed PASS: להתאים את tree של checkout ה־PR לראש שנבדק, לרענן main/הגנות, להסיר draft ולמזג בלי force או עקיפת מדיניות. Issues13/14/15/16 נסגרים רק לאחר קריטריוניהם. Issue12 כבר נסגר לפי PDF ב־Android;7 נשאר לחתימה.
6. מיזוג עשוי להפעיל Pages: לאמת מחדש75HTTP/SHA מול source marker החדש, לשמר alpha ו־latest.apk.38נכסי runtime לא השתנו בתיקוני Native; פרסום זהה אינו מהדורת תכונות חדשה.
7. להמשיך את BACKLOG. שמירת PDF דרך מערכת iOS נבדקת בנפרד בענף `work/ios-files-cell-save-20261110`. מבחן קודם מצא את Save-to-Files כ־Cell אך קיבל סרגל Options כראיית Files; זו בדיקה חלשה ואין ממנה PASS לשמירה. ניסויeab09e8/run42876796144 נכשל בקומפילציית אבחון (`XCUIApplication.bundleIdentifier` אינו API ציבורי), לא בהרצת המוצר. תיקון79f6e45 משתמש ב־label, מקמפל בדיקות לפני boot, דורש Save ממשי ואוסף PDF חדש מספק localStorage של הסימולטור. יש לרענן את הריצה לפי head זה ולבדוק בתים/עמודים לפני קבלה.

## חוזים, ראיות וסמכויות

SHA256 המשפטי הוא `de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9`; מועד האימות **2026-10-28**. אין שינוי חקיקה, הערות, אסמכתאות או תאריך. verify_release מאמת35בדיקות SHA/DOM/IDs/קישורים; זו אינה בדיקה משפטית.

[Android94](qa/mobile-2026-11-08/acceptance-94cdf7d.json) העביר9Linux/Android, מצב1.6MB→Activity1036–1200bytes, cache עוין, renderer recovery31/36 ו־PDF146עמודים שאומת עצמאית. [iPad94](qa/mobile-2026-11-08/ipad-window-94cdf7d.json) העביר חלון1032→375pt ופקדים44pt. [שיתוף4bc](qa/mobile-2026-11-08/ios-legacy-share-component-accepted.json) עבר16/iPad18.5; [PDFb916](qa/mobile-2026-11-08/ios-complete-pdf-component.json) עבר126עמודים וגם Poppler. אין לייחס formatter לשמירה ב־Files או למדפסת פיזית. [Android מצומצם](qa/mobile-2026-11-08/android-constrained-hardware.json) עברactual1.5GB/ליבה אחת; אין טענת1GB/OOM/כלל תהליכיWeb.

תיקונים, בדיקות, commits/PR, מיזוג ופרסום שעברו שערים מותרים אוטונומית. אין force-push, החלפת זהות חתימה, תג חתום או קישור APK קיים, ענן/Analytics/פרסומות או תשלום. חתימה פרטית, Apple Team/ASC, הצהרות בעלים ומכשיר פיזי הם פעולות חיצוניות אמיתיות בלבד, מפורטות ב־EXTERNAL_ACTIONS. אין צורך בהרצת Windows או התקנת כלים אצל המשתמש. סביבת Work זמינה שוב; גם כשהיא נעלמת GitHub API/Actions וענפי checkpoint מאפשרים המשך.
