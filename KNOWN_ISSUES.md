# תקלות ידועות ומגבלות כיסוי

| מזהה | היקף / מצב | ממצא ודרך המשך |
|---|---|---|
| QA-ANDROID26-ROW | תיקון בדיקה אומת גם ב־PR11/4ee | צילום הוכיח שקובץ JSON קיים; עץ A11y הוכיח שה־filename ב־depth17 ולשורת RecyclerView אין ACTION_CLICK. הקשת pointer לפי bounds של שם מדויק מאפשרת SAF אמיתי. אין צורך לשנות פורמט גיבוי או להחליש הרשאות |
| QA-ANDROID36-PRINT | פתוח בקבלה המלאה | lookup לפי ID מצא print_button מוסתר אך enabled; AOSP16 קובע GONE עד עדכון המסמך. גם כפתור גלוי עשוי להופיע בזמן Preparing preview. המתנה לעמוד Page n of total אפשרה PDF אמיתי במצב לרוחב בניסוי42726433709; מצב לאורך נכשל עם קריסת MediaProvider/FuseDaemon ואז יציאת תהליך reader, ללא חריגת Java באפליקציה שנמצאה. הסיבה המלאה אינה מוכחת; full API36 עדיין פתוח |
| QA-ANDROID36-SHARE | תיקון בדיקה אומת4ee | הוחזרה פעולת ACTION_CLICK של יעד sharesheet; אישור Intent ב־UID אחר עבר API36 לפני כשל PDF. אין להסיר את אישור הקבלה |
| DEPLOY-ENVIRONMENT | מגבלת workflow, לא הוכחת כשל אתר חי | env github-pages מתיר רק main/gh-pages; deploy מה־release branch נדחה. אין לשנות הגנה; פרסום gh-pages42718136476 וה־HTTP עברו. CI-003 מפריד verifier לקריאה בלבד מ־deployment workflow המוגן, ללא שינוי policy |
| SIGN-ANDROID | חסם חיצוני | המפתח הפרטי ההיסטורי אינו זמין; אין Debug כשדרוג.1.3.5 הציבורי נשמר |
| SIGN-IOS | חסם חיצוני | אין גישת Team/profiles/ASC לחתימה והפצה; סימולטור/unsigned archive בלבד |
| COVERAGE-IPAD-WINDOW | כיסוי חסר | rotation וגדלי Web נבדקו; Split View ומנהל החלונות לא הוכחו כאינטראקציה Native מלאה |
| COVERAGE-LOW-MEMORY | כיסוי חלקי | process recovery וקוד טיפול קיימים; sustained pressure וכלל תהליכי Web אינם מכוסים בכל חומרה |
| COVERAGE-PHYSICAL | לא נבדק | מכשירים פיזיים, TalkBack/VoiceOver אנושיים, מדפסת פיזית ורינדור במסמך Word חיצוני |
| LINKS-NATIVE | הבדל מוצדק | HTTPS נפתח לסעיף ב־Web; אין Universal/App Links מאומתים לתוך Native ואין Team ID מומצא |

הגלילה הלא־מכוונת של העמוד/התקנות שוחזרה ותוקנה: לפני התיקון64/35/32/17/3/6 מקרים כושלים בששת הרוחבים; אחרי התיקון0 בכל רוחב. טבלאות נתונים רחבות שומרות גלילה פנימית. פרטים: qa/mobile-2026-11-08/horizontal-layout-before-after.json.

ארטיפקטי Actions זמניים (Native iOS7ימים, האחרים בדרך כלל30, פריסה90); סיכומים ודיגסטים נשמרים ב־Git. היעלמות artifact אינה PASS או כשל חדש; אפשר לבנות מחדש מהמקור. אין ידיעה שהחוק מדויק משפטית מכוח מחזור זה, והמקור/מועד אימותו נשמרים.

NAV-006/PWA-001: שוחזרו יעד תקנות שהוסתר מתחת לחזרה ומטמון חסר שנספר כמלא כאשר נוסף נכס זר. התיקון הנוכחי ממתין לפרסום ולשערי CI; אין שינוי בקובץ המקור.
