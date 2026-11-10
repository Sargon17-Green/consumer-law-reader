# אבחון חלונות iPad — NATIVE-003

ענף work/ipad-window-resize-20261110 הוא ניסוי בדיקה נפרד מ־PR11 ומהפצת Web. בסיס706a3bc19f7a75026ccb2bac614816e12c5f5293. אין שינוי בקוד המוצר ואין טענת PASS לפני completed/log.

המבחן מפעיל Settings אמיתי בסימולטור iPad26.2, בוחר Multitasking & Gestures → Windowed Apps, מפעיל את היישום, מחפש14 ואז מבצע את מחוות resize של חלון המערכת. קבלה דורשת הקטנה מדודה של WKWebView בלפחות15%, רוחב מעל250, מטרות44px, שימור החיפוש ופעולת חזרה. CSS/שינוי גודל container בלבד אינם נחשבים בדיקת מנהל חלונות.

XCTest מצרף צילומי מסך אמיתיים ועצי נגישות לפני/אחרי הפעולות. אם Setting/handle אינו נגיש, יש לקרוא את הראיות ולתקן את האוטומציה; אין לטעון שחסר אישור משתמש או לגשת ל־private preference. אם שינוי גודל אינו מתרחש — הבדיקה נכשלת. בניסוי זה אין שינוי הגדרות במכשיר משתמש ואין פעולה בחשבון Apple.

מקורות רשמיים שנקראו ב־10.11.2026: https://developer.apple.com/videos/play/wwdc2025/208/ (מחוות resize בפינה הימנית התחתונה; הגדרת חלונות גמישים), https://support.apple.com/guide/ipad/work-with-multiple-windows-at-the-same-time-ipad08c9970c/ipados (Windowed Apps בהגדרות), https://developer.apple.com/documentation/xcuiautomation/xcuielement (מחוות ו־coordinates לפי אלמנט נמדד). המקורות אינם הוכחה שהמחווה כבר עברה בסימולטור זה.


ניסיון ראשון f35c1214 / run42765418790 נכשל רק בקריטריון שינוי הגודל: Windowed Apps נבחר בפועל, חיפוש/14 וחזרה הוצגו, מחוות touch לא הקטינה את החלון. artifact13739722986 SHA2561241ddce99ceb854e3cb21f1e8541c3fa8dc6ce44a154b19e9608cfcbcb8ae9b. בצילום2064×2752 ידית אפורה נראתה בפיקסלים2008..2054,2696..2742; אין להסיק הצלחת resize מעצם הופעתה. הגרסה הבאה מחליפה touch ב־pointer click-and-drag הציבורי של XCUICoordinate, מתעדת גם SpringBoard וצילום מיד אחרי המחווה לפני assertion, ודורשת שוב הקטנה אמיתית. אין שינוי מוצר או private API. מקור: https://developer.apple.com/documentation/xcuiautomation/xcuicoordinate .


ניסיון f61/run42767188687 הראה שהמחווה כן שינתה חלון, אבל במצב scaling: Window CGRect34,269.1,965,723.8; native-menu30.9×30.9 במקום44. לפיכך אין לכנותו עוד כשל מחווה בלבד. חבילת .app בפועל חסרה UISupportedInterfaceOrientations וכל וריאנט iPad. הניסוי הבא מוסיף הצהרת3כיווני iPhone ו־4כיווני iPad דרך build settings הרשמיים, ובדיקת XCTest של Info.plist הבנוי. אין נעילת כיוון או UIRequiresFullScreen. ההשערה היא שהצהרת הכיוונים תאפשר resize רציף במקום scaling; אינה PASS לפני מדידה. handle מערכת אמיתי נצפה ב־SpringBoard AX: identifier resize-grabber, label Resize חוק הגנת הצרכן, value Bottom Right; המחווה הבאה נצמדת אליו במקום להסתפק בגאומטריית app window.

מקורות Apple שנקראו: https://developer.apple.com/documentation/xcode/build-settings-reference (INFOPLIST_KEY_UISupportedInterfaceOrientations ו־_iPad), https://developer.apple.com/documentation/technotes/tn3192-migrating-your-app-from-the-deprecated-uirequiresfullscreen-key (תמיכה בכל כיווני המסך), https://developer.apple.com/documentation/BundleResources/Information-Property-List/UISupportedInterfaceOrientations . קובץ המקור המשפטי וה־Web אינם משתנים בניסוי.
