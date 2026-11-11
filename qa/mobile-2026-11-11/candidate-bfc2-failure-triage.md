# תוצאות מחזור bfc2 והמשך קבלה יחיד

תאריך: 11.11.2026. מקור אמת: ראיות GitHub Actions שהסתיימו, לא תיאור שיחה. תחולה על המאגר `Sargon17-Green/consumer-law-reader`, PR #11, ענף `fix/pastafari-date-android-20261028`.

## SHA וריצות שהוכרעו

- SHA שנבדק: `bfc2c828f0baba7c871de682f5fb3ee92a19466d`.
- [Source/Web/Android run 43060328220](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43060328220): **completed/success, 9/9 jobs**.
- [iOS run 43060328507](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/43060328507): **completed/failure, 2/6 jobs success**. כל ששת הפרופילים הגיעו למבחני UI והאפליקציות נבנו; אין אישור מועמד.

| פרופיל iOS | תוצאה | כשל מדויק / מסקנה |
|---|---|---|
| iPhone 16.0 | PASS | ריצת המבחן התפקודי על runtime 16 עצמו הושלמה; audit iOS17+ דולג כנדרש |
| iPhone 18.5 | PASS | תרחיש ה־fileImporter שנכשל במחזור קודם עבר; הכשל הקודם אינו מוכיח תקלה דטרמיניסטית |
| iPhone 26.2 | FAIL | job 130660823801; `ReaderUITests.swift:111`: Close בתצוגת print נלחץ, אך חלון ההדפסה נותר מוצג במשך30s; צילום מסך מראה UI print פעיל ופקדי app מושבתים |
| iPhone 26.2 XXXL | FAIL | job 130660823262; `ReaderUITests.swift:101`: selector `Page 1 of ` לא איתר עמוד. בארטיפקט המקורי ממחזור קודם התא של עמוד 1 נקרא `1` בצירוף `Pages 1-201`; אין הוכחת כשל rendering |
| iPad 18.5 | FAIL | job 130660823811; `ReaderUITests.swift:145`: `ActivityListView` קיים, אך אין Close נגיש תחת תת־העץ. צילום הסימולטור בעת הכשל מראה שכבת overlay בלי פעולות שיתוף גלויות; root cause לא הוכח |
| iPad 26.2 | FAIL | job 130660823930; `ReaderUITests.swift:145`: חיפוש Close בתת־העץ נכשל. צילום מראה כפתור X חזותי בתוך חלונית השיתוף, אך hierarchy מתוך `ActivityListView` לא כוללת כפתור זה. לפני שינוי `firstMatch` פרופיל זה עבר |

## שינויים במחזור הבא — אין לטעון PASS לפני completed

1. בדיקת תצוגת ההדפסה ב־iOS26 תזהה **שתי גרסאות AX אמיתיות**: `Page 1 of N` או `1` בצירוף `Pages 1-N`. בכל מקרה נדרש תא חיובי־ממדים, חלון הדפסה ומנגנון סגירה פעיל. צילום/AX יישמרו בכשל.
2. בדיקת Close של print תמשיך לדרוש היעלמות חלון print **וגם** הפעלת פקדי האפליקציה, עם צילום אחרי כשל. אין טיפול ייצור ספקולטיבי בהתנהגות UIKit; כשל iPhone26 נותר פתוח.
3. מבחן השיתוף יחפש Close בממשק האפליקציה הכולל ולא רק כצאצא של `ActivityListView`. נשמרים `isHittable` והדרישה להיעלמות השיתוף. נוסף צילום כשל והיררכיית AX מלאה. לא בוצעה עקיפה דרך הקשה על אזור שאינו כפתור.
4. **לא** משנים fileImporter של iPhone18.5 שעבר במחזור זה ללא ראיה נוספת; שומרים כיסויו במבחן.
5. אין שינוי ב־`original/Consumer_Protection_Law.html`, בפרטי הפצה, חתימה, package ID או URL ציבורי.

## שער מחייב אחד להמשך

- כשהקומיט הכולל תיקונים ותיעוד אלה נפתח ב־PR #11, ממתינים לריצות CI על אותו SHA; אין לדחוף קומיטים בין queued/in_progress לבין completed.
- דורשים 9/9 מקור/Android ו־6/6 iOS **על אותו SHA/tree**. כישלון בכל רכיב => לא למזג ולא לפרסם native. לא מאחדים תוצאות ממחזורי CI שונים.
- אם נותר כשל print Close או share appearance, חובה לחזור לארטיפקט `xcresult`, screenshot ו־AX של העבודה המסוימת. לתקן רק על סמך ההשוואה; אין להסיר assert, להסתפק בזיהוי חלון ריק או לשנות מימוש UIKit בלי סיבה הנדסית מאומתת.
- שמירת PDF ל־Files שהתקבלה בעבר בריצה [42968670868](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42968670868) היא **ראיה נפרדת** על SHA אחר. אין לראות בה קבלת המועמד הזה.
- מצב ההפצה נשאר: Web/PWA ציבורי; Android 1.3.5-beta חתום; 1.3.9 Native אינו חתום להפצה. פרטי הרשאות חסרים ב־`EXTERNAL_ACTIONS.md`.

## סדר קריאה לשיחה הבאה

1. ראש PR #11 וסטטוס ריצותיו בפועל.
2. `PROJECT_HANDOFF.md` ומסמך זה.
3. לוגי completed ו־`ios/ConsumerLawReaderUITests/ReaderUITests.swift` לפי SHA הנבדק.
4. תנאי קבלה ופעולות חיצוניות ב־`TESTING.md`, `BACKLOG.md`, `EXTERNAL_ACTIONS.md`.

אין לפתוח ענף/PR חלופי, ואין לעבור למחזור פיתוח חדש לפני הכרעת הישן.
