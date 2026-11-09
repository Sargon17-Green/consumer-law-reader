# תקלות ידועות ומגבלות כיסוי

| מזהה | היקף / מצב | ממצא ודרך המשך |
|---|---|---|
| QA-ANDROID26-ROW | תיקון בדיקה אומת בענף אבחון | צילום הוכיח שקובץ JSON קיים; עץ A11y הוכיח שה־filename ב־depth17 ולשורת RecyclerView אין ACTION_CLICK. הקשת pointer לפי bounds של שם מדויק מאפשרת SAF אמיתי. אין צורך לשנות פורמט גיבוי או להחליש הרשאות |
| QA-ANDROID36-PRINT | פתוח בקבלה המלאה | lookup לפי ID מצא print_button מוסתר אך enabled; AOSP16 קובע GONE עד עדכון המסמך. הבדיקה ממתינה כעת ל־refresh/isVisibleToUser. חייבים להוכיח שמירת PDF ממשית; פתיחת Print UI בלבד אינה מספיקה |
| QA-ANDROID36-SHARE | פתוח באבחון | בדיקה לא מצאה יעד בשטח sharesheet במחזור אבחון, אף שהצליחה קודם ב־2f91d12. אין ראיה לכשל שיתוף באפליקציה עצמה. אין להסיר את בדיקת קבלת ה־Intent ב־UID אחר; נשמר אישור הקבלה בסיום |
| DEPLOY-ENVIRONMENT | מגבלת workflow, לא הוכחת כשל אתר חי | env github-pages מתיר רק main/gh-pages; deploy מה־release branch נדחה. אין לשנות הגנה; יש לבדוק פרסום gh-pages הרגיל ו־HTTP של כל הנכסים |
| SIGN-ANDROID | חסם חיצוני | המפתח הפרטי ההיסטורי אינו זמין; אין Debug כשדרוג.1.3.5 הציבורי נשמר |
| SIGN-IOS | חסם חיצוני | אין גישת Team/profiles/ASC לחתימה והפצה; סימולטור/unsigned archive בלבד |
| COVERAGE-IPAD-WINDOW | כיסוי חסר | rotation וגדלי Web נבדקו; Split View ומנהל החלונות לא הוכחו כאינטראקציה Native מלאה |
| COVERAGE-LOW-MEMORY | כיסוי חלקי | process recovery וקוד טיפול קיימים; sustained pressure וכלל תהליכי Web אינם מכוסים בכל חומרה |
| COVERAGE-PHYSICAL | לא נבדק | מכשירים פיזיים, TalkBack/VoiceOver אנושיים, מדפסת פיזית ורינדור במסמך Word חיצוני |
| LINKS-NATIVE | הבדל מוצדק | HTTPS נפתח לסעיף ב־Web; אין Universal/App Links מאומתים לתוך Native ואין Team ID מומצא |

הגלילה הלא־מכוונת של העמוד/התקנות שוחזרה ותוקנה: לפני התיקון64/35/32/17/3/6 מקרים כושלים בששת הרוחבים; אחרי התיקון0 בכל רוחב. טבלאות נתונים רחבות שומרות גלילה פנימית. פרטים: qa/mobile-2026-11-08/horizontal-layout-before-after.json.

ארטיפקטי Actions זמניים (Native iOS7ימים, האחרים בדרך כלל30, פריסה90); סיכומים ודיגסטים נשמרים ב־Git. היעלמות artifact אינה PASS או כשל חדש; אפשר לבנות מחדש מהמקור. אין ידיעה שהחוק מדויק משפטית מכוח מחזור זה, והמקור/מועד אימותו נשמרים.
