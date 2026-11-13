# מחזור b41b3c40 — בידוד שיתוף והוכחת פעולות בפועל

מועד: 12.11.2026. פרויקט `Sargon17-Green/consumer-law-reader`, PR #11, ענף יחיד `fix/pastafari-date-android-20261028`.

## שער QA שהושלם — קוד b41b3c40

- HEAD שנבדק `b41b3c40ef9471ba10e302469c05897e10b3f75f`, tree `bd199caba2f7d50cfefa481f44cb01b37dcb3e42`.
- [Linux/Web/Android 43303378028](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43303378028): `completed/success`, 9/9.
- [iOS 43303378173](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43303378173): `completed/failure`, 1/6 full jobs success. עברה: iPhone iOS16.0; חמש עבודות אחרות נכשלו ב־UI, לא בבנייה. **אין קבלה משולבת.**

| פרופיל | שיתוף אחרי Files בלבד | אחרי Print בלבד | Cold share | רצף מלא |
|---|---|---|---|---|
| iPhone16 | PASS | PASS | PASS | PASS |
| iPhone26.2 | PASS | PASS | PASS | FAIL אחרי Cancel של Files — preflight hit-testing |
| iPhone26.2 XXXL | FAIL אחרי Close של share — בדיקת היעלמות | PASS | PASS | PASS |
| iPhone18.5 | FAIL עוד ב־header `isHittable` | FAIL עוד ב־header `isHittable` | PASS | FAIL אחרי Files |
| iPad18.5 | FAIL עוד ב־header `isHittable` | FAIL עוד ב־header `isHittable` | PASS | FAIL אחרי Files |
| iPad26.2 | FAIL: בורר Files ללא Cancel `isHittable` | PASS | PASS | FAIL אחרי Files |

## מסקנות נתמכות בלוגים

1. **לא הוכח כשל שיתוף אוניברסלי.** iPhone16 עבר את ארבעת הרצפים המלאים. iPhone26 עבר שלושה מארבעה. XXXL עבר cold/Print/full ונכשל רק בשלב אישור סגירת השיתוף אחרי Files (הודפס `SHARE_ISOLATION_CLOSE_after-Files-only`).
2. בדיקות בידוד על iOS18.5 נפלו בסעיף `menu.isHittable` עוד **לפני הקשה על תפריט פעולות**; מנגד מבחן cold ומבחן full הצליחו לפתוח את ממשק האפליקציה. Apple מגדירה `isHittable` כיכולת לחשב נקודת לחיצה, ולא כראיה ליכולת להפעיל פקד בכל מסלול תנועה. מקור: https://developer.apple.com/documentation/xcuiautomation/xcuielement/ishittable.
3. אחרי Cancel של Files התרחיש המלא דורש `!cancel.isHittable && !picker.isHittable && menu.isHittable && share.isHittable`. אלו ארבע בדיקות AX נוספות ב־DocumentManager/SwiftUI שחלקן נשארות stale או יקרות; כאשר הן נכשלות לא נעשה ניסיון share. זהו **כשל בטרום־תנאי מבחן**, לא הוכחה שהשיתוף במוצר מקולקל.
4. קיימים גם כשלים אמיתיים לא מוכרעים: iPad26.2 Cancel של system Files לא ניתן לזיהוי בחלק מהריצות; iPad Windowing UI נכשל אחרי resize/ביטול Menu; ב־XXXL נצפתה לפעמים אי־היעלמות של ActivityListView אחרי Close. אין להכריע אותם על בסיס סברה.

## שינוי מבחן ממוקד ומוגבל

- **אין שינוי בקוד המוצר.** XCTest מבצע כעת tap ממשי על מרכז Share אחרי אימות `exists`, `isEnabled`, מידות של לפחות 44x44. הבדיקה אינה מסתפקת ב־tap: היא ממשיכה לחייב `ActivityListView`, כפתור Close אמיתי עם `isHittable`, לחיצה עליו והיעלמות החלונית. אם בורר Files עדיין חוסם את Share, חלונית השיתוף לא תיפתח והבדיקה תיכשל בשער שאינו ניתן לעקיפה.
- הבדיקות העצמאיות אינן נופלות לפני פעולה אמיתית רק בשל `isHittable` של Menu ב־iOS18.5: במקום זאת הן מקישות ב־coordinate ותובעות הופעת הפעולה הייעודית (`Print` או `Restore`).
- אין הגדלת timeout שרירותית, שינויי חתימה או תוכן משפטי. כל מסלולי XCTest המקוריים נשארים במקומם.

## ההמשך המחייב

לא להזיז HEAD עד ששתי ריצות ה־CI החדשות יסתיימו. לקרוא את ה־SHA העדכני וסטטוס 9+6 jobs, ולאסוף logs ו־xcresult עבור כל FAIL. לא להסתמך על PASS מענף/קומיט אחר, לא למזג לפני 15/15 completed/success על אותו tree ומעבר שחרור. כאשר נשארים כשלים במצבי UIKit, לשקול תיקון מוצר רק עם הוכחה מצילומים/לוגים ולא כחזרה על שינויי סלקטור.
