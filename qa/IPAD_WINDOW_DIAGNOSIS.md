# אבחון חלונות iPad — NATIVE-003

ענף work/ipad-window-resize-20261110 הוא ניסוי בדיקה נפרד מ־PR11 ומהפצת Web. בסיס706a3bc19f7a75026ccb2bac614816e12c5f5293. אין שינוי בקוד המוצר ואין טענת PASS לפני completed/log.

המבחן מפעיל Settings אמיתי בסימולטור iPad26.2, בוחר Multitasking & Gestures → Windowed Apps, מפעיל את היישום, מחפש14 ואז מבצע את מחוות resize של חלון המערכת. קבלה דורשת הקטנה מדודה של WKWebView בלפחות15%, רוחב מעל250, מטרות44px, שימור החיפוש ופעולת חזרה. CSS/שינוי גודל container בלבד אינם נחשבים בדיקת מנהל חלונות.

XCTest מצרף צילומי מסך אמיתיים ועצי נגישות לפני/אחרי הפעולות. אם Setting/handle אינו נגיש, יש לקרוא את הראיות ולתקן את האוטומציה; אין לטעון שחסר אישור משתמש או לגשת ל־private preference. אם שינוי גודל אינו מתרחש — הבדיקה נכשלת. בניסוי זה אין שינוי הגדרות במכשיר משתמש ואין פעולה בחשבון Apple.

מקורות רשמיים שנקראו ב־10.11.2026: https://developer.apple.com/videos/play/wwdc2025/208/ (מחוות resize בפינה הימנית התחתונה; הגדרת חלונות גמישים), https://support.apple.com/guide/ipad/work-with-multiple-windows-at-the-same-time-ipad08c9970c/ipados (Windowed Apps בהגדרות), https://developer.apple.com/documentation/xcuiautomation/xcuielement (מחוות ו־coordinates לפי אלמנט נמדד). המקורות אינם הוכחה שהמחווה כבר עברה בסימולטור זה.
