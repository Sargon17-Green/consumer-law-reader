# כניסה לפרויקט והמשך עבודה

**Sargon17-Green/consumer-law-reader** הוא קורא חוק הגנת הצרכן, התשמ״א–1981: Android WebView, SwiftUI/WKWebView ו־Web/PWA משותף. אין לערבב עם פרויקט לוח השנה. מפרסמים ערוץ בשל מוקדם וממשיכים; אין צורך בשיחה או בזיכרון חיצוני.

## לקרוא תחילה

[מצב](IMPLEMENTATION_STATUS.md), [63 דרישות](PRODUCT_REQUIREMENTS.md), [קטלוג](docs/requirements.json), [BACKLOG](BACKLOG.md), [תקלות](KNOWN_ISSUES.md), [ארכיטקטורה](ARCHITECTURE.md), [בדיקות](TESTING.md), [הפצה](RELEASE_PROCESS.md), [היסטוריה](RELEASE_HISTORY.md), [החלטות](DECISIONS.md), [פעולות חיצוניות](EXTERNAL_ACTIONS.md).

## פרסום וראיות

- **Web/PWA תיקון3 פורסם:** [reader](https://sargon17-green.github.io/consumer-law-reader/reader/), הוספה למסך הבית. מקורcca785ed8b1f3d4c96bf25c0eb50e77b04899566 ומטמון453decfde812ec9b. [75HTTP/SHA עברו שוב](qa/mobile-2026-11-08/public-web-readonly-recheck.json), כולל alpha וה־APK, בריצה42859574863.
- **Android הציבורי1.3.5-beta:** [latest.apk](https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk). אין מפתח פרטי מקורי נגיש שאומת; [תחום החיפוש](qa/mobile-2026-11-08/signing-availability-scope.json). מועמד1.3.9-dev/code17 הוא Debug/unsigned בלבד.
- **iOS1.3.9/build17:** סימולטורים ו־device archive לא חתום; אין IPA חתום או TestFlight.
- [94cdf7d](qa/mobile-2026-11-08/acceptance-94cdf7d.json) העביר9Linux/Android ושלושה מחמישה iOS; נכשל בסגירת שיתוף ב־16/iPad18.5. Android94 כולל IME/cache עוין/PDF146עמודים; iPad26 עבר את כל רצף שינוי החלון. אין למזג94 על סמך הצלחות חלקיות.
- [4bc27af](qa/mobile-2026-11-08/ios-legacy-share-component-accepted.json) העביר את שני תרחישי השיתוף הישנים ומבחן callback ישן. [b916235](qa/mobile-2026-11-08/ios-complete-pdf-component.json) העביר PDF UIKit מלא126עמודים; Poppler נפרד אימת bytes/page count וטקסט. אין טענת Files-save UI או מדפסת פיזית.
- [Android26 בתצורת1.5GB/ליבה אחת](qa/mobile-2026-11-08/android-constrained-hardware.json) עבר בנפרד; אין טענת1GB/OOM/כל תהליכי Web.

## מאיפה ממשיכים

1. לרענן קודם את [PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11), ראשי הענפים והריצות. PR body מציג קבלה עדכנית ו־SHA/tree של הריצה הסופית; זו הפניה קבועה, לא תלות בשיחה. הענף `fix/pastafari-date-android-20261028` מרכז את המועמד; `docs/mobile-release-evidence-20261110` הוא checkpoint. בסיס main המקורי016b3de352dabe97f51b34b78ff803965b6cd40d.
2. **הצעד הבא:** לתקן את ממצאי [027](qa/mobile-2026-11-08/candidate-027-followup.json) לפני רגרסיה מאוחדת חדשה: Linux8/9PASS, API36 offline IME נכשל; iPad26.2 Print Close נכשל למרות מיקום מגע נכון; iPhone18.5 ReferenceError lawMobile ב־lifecycle בעוד UI עבר. iPhone26.2/16 ו־iPad18.5 עברו; XXXL עדיין רץ בזמן checkpoint. ניסוי Android bfcb7e1/run42870233731 מאתר את חלון היישום אחרי IME (850 חשף שחלון פעיל הוא המקלדת); iOS f522c22/run42870553619 מוסיף trace לפקודת JS, ו־278d13e/run42870543669 בודק Print Close/Share-to-Files. קודם לרענן את תוצאותיהם; אין להריץ עותק זהה ללא השערה חדשה.
3. לאחר תיקונים מוכחים, לקבל את המועמד המאוחד בכל15 השערים —9Linux/Android ו־6iOS. נוספו בדיקות מקלדת תוכנה אמיתית וגודל מערכת accessibility XXXL. אין PASS מריצה queued/in_progress ואין צורך להפעיל ריצה זהה נוספת.
4. רכיבי המקור:4bc27af9cee6018008baf0cf37c82a06eec65473 לשיתוף, b91623549a235597f3005eb3100a72c274c0565b ל־PDF מלא,0c9507a5b486a5e28dd4aeec2743a5f7db255a03 לבדיקת IME/גודל. ענפי work הם ניסויי אבחון; המועמד מכיל רק קוד/בדיקות קבועות ו־workflow הקבלה המורחב, בלי filters מקצרים. ניסוי הגודל42858470735 נבדק בנפרד, בלי להסיק קבלה מהמתנה.
5. לאחר completed PASS והתאמת tree, לבדוק הגנות, להסיר draft ולמזג. Issues13/14/15 נסגרים רק לאחר הקריטריונים. Issue12 כבר נסגר לפי קבלת PDF Android; Issue7 נשאר לחתימה. אם main השתנה, לרענן בסיס ולבדוק מחדש בלי לדרוס עבודה מקבילה.
6. מיזוג עשוי להפעיל Pages. יש לאמת את75HTTP מול source marker החדש ולשמר alpha/APK. Runtime Web זהה אינו מהדורת תכונות חדשה.
7. להמשיך את BACKLOG; לחתום ולהפיץ Native רק אם מקור המפתח/Team נגיש ומורשה. אין צורך בהרצות או התקנות במחשב המשתמש.

## חוזים וסמכויות

SHA256 המשפטי נשאר `de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9`; מועד האימות **2026-10-28**. verify_release מעביר35 בדיקות SHA/DOM/IDs/קישורים. אין שינוי חקיקה/פרשנות/הערות/תאריכים, ענן, Analytics או פרסומות.

Parcel cache זמני ומותנה באותה התקנת OS/app/provider; אינו גיבוי נייד. כשל חוזר למיקום לוגי והגדרות נשמרות בנפרד. collector פרטי פועל רק באמולטור userdebug/UID0/SELinux Enforcing ומאמת בתים; אין החלשת debuggable.

תיקונים, בדיקות, PR, מיזוג ופרסום שעברו שעריהם מותרים אוטונומית. אין force-push, שינוי חתימה או הצגת Debug/סימולטור כהפצה. חתימה פרטית, Apple Team/ASC, זכויות/תשלום ומכשיר פיזי אינם מומצאים; הפעולות המדויקות ב־EXTERNAL_ACTIONS. אם סביבת Work זמנית נעלמת, הקוד בענפים, GitHub API ו־Actions מאפשרים המשך בלי התקנת כלים אצל המשתמש.

## עדכון checkpoint — קודם לקרוא לפני הפעלת ריצות נוספות


עדכון completed:027iOS הסתיים4/6PASS. פרופיל מערכת accessibility XXXL עבר בפועל (input18,422,366,54; keyboard0,583,402,233), כולל8מבחני WK/policy ו־UI מלא274.357שניות. iPad26 Print Close ו־iPhone18.5 lifecycle נשארו כשלי קבלה. Android bfcb7e1 עבר26/36 אך31 לא הקליד אחרי ACTION_SET_TEXT;94dabd5/run42871943171 בודק מחיקה במקש Native. אבחון lifecycle תוקן ל־475d9fa/run42871844738 לאחר שגיאת קומפילציה ב־trace בלבד.

בדיקת checkpoint a06c91f/run42871114992/job130022342617 הסתיימהPASS:12מסמכים/63דרישות,52יחידות,35SHA/DOM,500UTF16 ותאריך fallback. [תמונות מקוריות קבועות](qa/mobile-2026-11-08/screens/README.md) נשמרו ב־Git. אין להסיק מכך קבלה של Native.

ראשי הניסויים והתרחישים המלאים: [candidate-027-followup.json](qa/mobile-2026-11-08/candidate-027-followup.json). מקור המועמד עדיין PR11/027; ענף docs מכיל את הראיות העדכניות. לאחר תוצאה חדשה יש לעדכן את הקטלוג, לא להסתמך על מצבי pending ההיסטוריים למעלה.
