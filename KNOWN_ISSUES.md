# תקלות ידועות ומגבלות כיסוי

עודכן ב־11.11.2026. [מצב](IMPLEMENTATION_STATUS.md), [BACKLOG](BACKLOG.md).

**הבהרת מצב לאחר קבלת 11.11:** [דו"ח חדש](qa/mobile-2026-11-11/completed-acceptance-triage-20261111.md) מוכיח source/Android 9/9 success מול iOS 3/6 success. נותרו שלושה כשלי UI מדויקים: XL/XXXL print-preview, iPhone18.5 שחזור מ־Files, iPad18.5 Close בשיתוף. אין PASS מאוחד. בניגוד לנתון ההיסטורי בטבלה מטה, Save-to-Files *נבדק בהצלחה בנפרד* ב־iPhone26.2 ב־[run42968670868](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42968670868), כולל PDF מקומי 136 עמודים וקובץ חדש. עדיין לא נבדקו מדפסת פיזית, כל מערכות iOS או נגישות Tagged PDF.

| מזהה | מצב | ראיה והמשך |
|---|---|---|
| QA-IME-027 | עבר ברכיב31; קבלה מאוחדת פתוחה |6d העבירonline/offline עם פוקוס/גאומטריה לפני מקשים ומחיקה Native;26/36 נבדקים במועמד המאוחד. [ראיות](qa/mobile-2026-11-11/components-accepted.json) |
| IOS-PRINT-027 | c853 עבר UI מלא; קבלה מאוחדת פתוחה | המתנה לעמוד preview ממשי ו־Close מוכן עברה348.896s בלי DEBUG delegate. לא הוכח גורם UIKit בלעדי; אין החלשת assertion. [ראיות](qa/mobile-2026-11-11/components-accepted.json) |
| IOS-LIFECYCLE-027 / Issue16 | guard מומש וממתין; גורם הכשל המקורי טרם הוכח | iPhone18.5/027 נכשל;200 העביר lifecycle ועוד8טעינות Native. generation guard מונע Ready ישן; סיבת הכשל המקורי לא יוחסה בלעדית. ממתין לקבלת6פרופילים ומיזוג |
| IO-002 / Issue15 | תיקון שיתוף עבר ברכיב; קבלה כוללת פתוחה | ב־545 iOS16 נשאר sharesheet אחרי Close ממשי, בעוד iPad18.5 עבר. חיבור completion ל־SwiftUI לפי UUID, עם המתנת Close מפורשת, עבר בשני המכשירים ב־4bc. אין להציג selector כגורם היחיד. [לפני](qa/mobile-2026-11-08/ios-legacy-share-diagnosis.json), [אחרי](qa/mobile-2026-11-08/ios-legacy-share-component-accepted.json) |
| DATA-003 / Issue14 | Android94 עבר; סגירה אחרי מיזוג מאומת | Binder קרס ב־06 במצב1.2MB. AtomicFile והפניה קטנה עברו בכל3API עם cache עוין. [קבלה94](qa/mobile-2026-11-08/acceptance-94cdf7d.json) |
| NATIVE-003 / Issue13 | iPad26/94 עבר במלואו | scaling וחפיפת SystemClose תוקנו;375pt/44pt/תפריט/שיתוף/סגירה/תוצאה גלויה לפני tap עברו. [ראיה](qa/mobile-2026-11-08/ipad-window-94cdf7d.json) |
| IO-003 / Issue12 | Android התקבל ו־Issue נסגר | PDF146עמודים וקובצי QA אומתו עצמאית. סיבת MediaProvider/FUSE ההיסטורית לא הוכחה ואין טענת שינוי במערכת. [ראיה](qa/mobile-2026-11-08/android-private-exports-94cdf7d.json) |
| IO-003 iOS | formatter מלא התקבל ברכיב; Files-save UI נפרד | UIKit126עמודים אומת גם ב־Poppler. לא נבדקה שמירה בממשק Files או מדפסת פיזית. [ראיה](qa/mobile-2026-11-08/ios-complete-pdf-component.json) |
| NATIVE-002 / A11Y | XXXL ו־IME iOS עברו ברכיב; קבלה כוללת כשלה | Android IME עבר; נוספו assertions של מקלדת תוכנה iOS ושדה מעליה, ופרופיל מערכת XXXL. אין PASS לפני completed; אין כיסוי לכל cutout/מקלדת |
| COVERAGE-LOW-MEMORY | חלקי ומדוד | Android26 עבר1.5GB/ליבה אחת; renderer recovery31/36 עבר. אין טענת1GB/OOM/לחץ ממושך/סך תהליכיWeb |
| COVERAGE-PHYSICAL | לא נבדק | מכשירים פיזיים, VoiceOver/TalkBack אנושיים, מדפסת וקוראWord חיצוני |
| SIGN-ANDROID / SIGN-IOS | גישה חיצונית חסרה | לא אומת מפתח Android המקורי נגיש; אין Team/profiles/ASC. אין Debug כשדרוג, IPA חתום או TestFlight |
| LINKS-NATIVE | הבדל מתועד | HTTPS מוביל לסעיף ב־Web; Universal/App Links לתוך Native אינם מאומתים |
| DEPLOY-ENVIRONMENT | חוזה פרסום | github-pages מתירmain/gh-pages; verifier בענף עבודה הוא GET בלבד. אין לעקוף הגנה |

הגלילה הלא מכוונת שוחזרה ותוקנה:64/35/32/17/3/6 כשלי root לפני,0 בכל אחד מששת הרוחבים אחרי. טבלאות רחבות שומרות גלילה פנימית נגישה. [ראיה](qa/mobile-2026-11-08/horizontal-layout-before-after.json).

SEARCH-005 פורסם ב־Web תיקון3 ועבר5רצפי DOM; Android94 ו־iPad26 חזרה עברו בהיקפם. [75HTTP חיים עברו שוב](qa/mobile-2026-11-08/public-web-readonly-recheck.json). אין צורך בפרסום Web זהה בגלל שינוי Native.

אין להסיר רגרסיות SAF26/depth17 או cross-UID share36 כדי לקצר ריצה. ארטיפקטי Actions זמניים; מזהי מקור/run, גיבובים, מגבלות וסיכומים קבועים נשמרים ב־Git. היעלמות artifact אינה PASS או כשל חדש. PDF שנבדק אינו בהכרח tagged; אין אישור נגישות כולל או בדיקה משפטית.

בדיקת Files נפרדת:060fbac/run42873707617 עבר תנאי חלש של navigationBar, ואינו PASS לשמירה. eab09e8/run42876796144 נכשל בקומפילציית בדיקה בלבד עקב API bundleIdentifier לא נתמך.79f6e45 מתקן ל־label, מקמפל tests לפני boot ודורש Save וקובץ חדש מקומי. אין לייחס כשל בדיקה זה ליכולת המוצר או להכריז Files-save PASS.
