# בדיקת hit-testing לכותרת iPad בחלון מוקטן

בסימולטור iPad26.2/run42772416090 התיקון metadata שמרNativeMenu44×44, אך screenshot13742524176/D827060D-711A-4CF4-AE33-2E34D9748B20.png (SHA171b3f57fa79eae9432ace6f345e01e9536ee01f33162287533a4d24cae6f6e1) מציג פקדי חלון מעל חלק מהכפתור. אין להסיק ממסגרת AX גדולה שהכפתור נגיש.

הניסוי הזה מבוסס06e5533 ואינו משנה קוד מוצר: actual WindowedApps resize, tap NativeMenu, דרישה שפעולתPrintמופיעה, סגירה, tapShare ודרישה לממשקActivityאמיתי. נשמרים screenshots+AX של האפליקציה ושלSpringBoard. המבחן הקיים שלquery/selectedresultלפניtapנשמר.

Apple HIG https://developer.apple.com/design/human-interface-guidelines/windows דורש להזיזפקדים כאשרwindowcontrols מופיעים. WWDC https://developer.apple.com/videos/play/wwdc2025/282/ מציגlayoutguideעםhorizontalcorneradaptation; לאמיישמיםפתרוןלפנישחזור.

אין כאןבדיקתמכשירפיזי,חתימהאוTestFlight. אםtapעובר איןלכנותאותוכשלתפקודימאומת; ישלתעדהבדלביןגאומטריהלביןפעולהאמיתית.
