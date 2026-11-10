# תקלות ידועות ומגבלות כיסוי

עודכן ב־10.11.2026. מצב קבלה ופרסום ב־[IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md); כל דרישה שלא הושלמה נשמרת ב־[BACKLOG](BACKLOG.md) ובקטלוג.

| מזהה | מצב | ממצא ודרך המשך |
|---|---|---|
| DATA-003 / Issue14 | תיקון רכיב אומת; קבלה משולבת פתוחה | ב־06/API36 נשלחו 1,204,952 בתים ב־Activity state ונגרמה TransactionTooLargeException. AtomicFile פרטי והפניה קטנה עברו ב־4819/API26/31/36. בדיקות adversarial נוספות ממתינות לרגרסיה המשולבת. [לפני](qa/mobile-2026-11-08/android-binder-state-before.json), [אחרי](qa/mobile-2026-11-08/android-state-cache-accepted.json) |
| NATIVE-003 / Issue13 | פעולות לאחר resize עדיין לא התקבלו | orientations תיקנו scaling. לחיצה אמיתית בניסוי 2e88de9 הוכיחה חסימה בידי SystemClose. corner inset ב־0d עבר תפריט ושיתוף אמיתיים בחלון375pt/כפתורים44×44; הריצה נכשלה בחזרה משום שהשיתוף נשאר פתוח.31b דורש סגירה מפורשת והיעלמותו. אין קבלה משולבת עדיין. [לפני](qa/mobile-2026-11-08/ipad-header-occlusion-before.json), [המשך](qa/mobile-2026-11-08/ipad-window-hit-test-progress.json) |
| QA-ANDROID36-PRINT | PDF מלא עבר; אין טענה שתוקן MediaProvider | כשל היסטורי היה abort של MediaProvider/FUSE ולא חריגת Java בקורא. שורש pf_setattr לא הוכח. לאחר בידוד איסוף QA ל־files פרטי, portrait/landscape עברו בנפרד; ריצת 4819 המלאה שמרה שני PDF בני146 עמודים. [אבחון](qa/mobile-2026-11-08/android-print-preview-diagnosis.json), [ייצוא מאומת](qa/mobile-2026-11-08/android-private-exports-accepted.json) |
| QA-EVIDENCE-PRIVATE | collector מתוקן עבר רכיב4819 | run-as לא מורשה באפליקציה שאינה debuggable; exec-out עלול להחזיר טקסט שגיאה ב־exit0. collector מוגבל לאמולטור userdebug/SELinux enforcing, בודק stat/magic/גודל/SHA. אין לקבל ADB error כתמונה או PDF |
| NATIVE-002 | פער אימות | יש טיפול insets ו־IME, אך API26 עבר עם IME אמיתי ו־Back;31 online עבר ו־offline נכשל בהנחת fixture ששדה משוחזר גלוי. תיקון QA מגלגל לשדה לפני מגע. אין עדיין ראיה מספקת לכל תרחישי מקלדת תוכנה/מסכים. אין להציג DOM viewport כבדיקת מקלדת Native |
| COVERAGE-LOW-MEMORY | חלקי | renderer termination/recovery אמיתי עבר API31/36; אינו מבחן OOM או עומס זיכרון מתמשך על כלל תהליכי Web |
| COVERAGE-PHYSICAL | לא נבדק | מכשירים פיזיים, בדיקות אדם VoiceOver/TalkBack, מדפסת פיזית ורינדור בקורא Word חיצוני |
| SIGN-ANDROID | חסם חיצוני | המפתח ההיסטורי אינו זמין; הציבורי1.3.5-beta נשמר ואין Debug כשדרוג |
| SIGN-IOS | חסם חיצוני | אין Team/profiles/ASC מורשים; סימולטור ו־unsigned archive בלבד |
| LINKS-NATIVE | הבדל מתועד | HTTPS נפתח לסעיף ב־Web; אין Universal/App Links מאומתים לתוך Native |
| DEPLOY-ENVIRONMENT | חוזה פרסום | github-pages מתיר רק main/gh-pages. אין לעקוף הגנה זו. verifier לקריאה בלבד יכול לרוץ בענף release; הפרסום עצמו ו־HTTP צריכים להיות מאומתים בנפרד |

הגלילה הלא מכוונת שוחזרה ותוקנה: לפני התיקון64/35/32/17/3/6 כשלי root בששת הרוחבים; אחרי התיקון0 בכל רוחב. טבלאות נתונים רחבות שומרות גלילה פנימית נגישה. [ראיה](qa/mobile-2026-11-08/horizontal-layout-before-after.json).

SEARCH-005: raw scroll השאיר את סעיף14 מחוץ לתוצאות לאחר reflow. התיקון עבר חמישה רצפי DOM ופורסם ב־Web תיקון3. אין פער פרסום Web פתוח; Native נשאר בשער קבלה נפרד.

תיקוני QA היסטוריים נשמרים: ב־API26 שורת filename של SAF נמצאת ב־depth17 ללא ACTION_CLICK, ולכן משתמשים ב־bounds של שם מדויק; ב־API36 אישור יעד sharesheet נבדק ב־UID אחר. אין להסיר את אימות הקבלה או להחליש הרשאות כדי לקצר בדיקה.

ארטיפקטי Actions מוגבלים בזמן: iOS7ימים, האחרים בדרך כלל30 ופריסה90. מזהי run/commit, דיגסטים וסיכומים קבועים נשמרים ב־Git; אפשר לשחזר מהמקור. היעלמות artifact אינה PASS או כשל חדש. קובץ PDF שנבדק אינו tagged; אין לייחס לו אישור נגישות למסמך PDF. מחזור זה אינו אימות משפטי, והמקור ומועד אימותו נשמרים.
