# מצב מימוש, אימות ופרסום

עודכן10.11.2026. קטלוג62 הדרישות ב־[docs/requirements.json](docs/requirements.json) הוא מקור המצב המובנה; [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md) נגזר ממנו. מימוש, אימות ופרסום הם מצבים נפרדים.

| ערוץ | הקבלה האחרונה שהסתיימה | מה פורסם בפועל |
|---|---|---|
| Web/PWA1.3.9-dev | על706a3bc:47unit,35SHA/DOM,Node500,4רוחבים,32axe,66תקנות ומטמוןoffline אמיתי | תיקון2/sourcec3e9d9e;75GET/SHA כולל owner/alpha/APK. [reader](https://sargon17-green.github.io/consumer-law-reader/reader/) מאפשר הוספה למסך הבית |
| Android1.3.9-dev/code17 | על706a3bc: API26/31/36 online/offline, SAF/שיתוף/העדפות ושניPDF146עמודים ב־API36 | הציבורי נשאר1.3.5-beta בחתימה המקורית. אין APK חדש חתום לשדרוג |
| iOS1.3.9/build17 | על706a3bc: כל4jobs עברו, iPhone26.2/iPad26.2/iPhone18.5/iPhone16.0, XCTest/XCUITest ו־archive מכשיר לא חתום | אין IPA חתום או TestFlight |

ראיות קבלה: [Linux706](qa/mobile-2026-11-08/acceptance-706a3bc-linux.json), [iOS706](qa/mobile-2026-11-08/acceptance-706a3bc-ios.json), [HTTP חי](qa/mobile-2026-11-08/public-web-patch-http-verification.json), [תוצר הפרסום](qa/mobile-2026-11-08/web-patch-candidate.json). מועמד706 נבדק ב־merge-ref ed7494e0a1fd2c3c2ae80f6929456e30872beaef; שני trees זהים539895887cecddd5c497f4aea8cf1dd1dc6ff1d5.

## המשך משולב — אינו מכוסה אוטומטית בראיות706

- **NATIVE-003/Issue13:** שחזור iPad הוכיח scaling וכפתור30.9pt. הצהרת orientations ב־project.yml תיקנה התאמה אמיתית: viewport1032→375pt, כפתור44×44. [ניסוי81b5f77](qa/mobile-2026-11-08/ipad-window-resize-accepted.json) עבר באופן ממוקד; רגרסיית4סימולטורים של המועמד המשולב נדרשת.
- **SEARCH-005:** בחזרה לתוצאות לאחר הקטנת חלון, סעיף14 נשמר אך היה מחוץ למסך ביותר מ־2800px. התיקון שומר תוצאה נבחרת ו־offset ומחשב מיקום חדש בעת שינוי רוחב/גובה/גופן; במבנה זהה נשמר המיקום הקודם. [לפני](qa/mobile-2026-11-08/search-layout-before.json)/[אחרי מקומי](qa/mobile-2026-11-08/search-layout-after-local.json) מתעדים DOM אמיתי; אין ייחוס dirty source ל־CI. עדיין לא פורסם.
- **ראיות Android פרטיות:** ניסוי Print fresh portrait/landscape עבר בתוך האפליקציה, אך run-as לא הורשה ולכן bytes שיוצאו לא אומתו. האיסוף החדש מוגבל לאמולטור userdebug/SELinux enforcing, מאמת stat/magic/SHA ואינו משנה debuggable או הרשאות מוצר. API36 חייב לייצא PDF זהה לגיבוב Native כדי לעבור.
- **התאוששות renderer:** תהליך WebView הופסק בפועל ב־API31/36 והאפליקציה התאוששה לסעיף14 וגופן24; [ניסויc08](qa/mobile-2026-11-08/android-renderer-diagnosis.json) נכשל כוללנית באיסוף ראיות. הרגרסיה המשולבת מוסיפה גם בחירת חיפוש ושחזור השאילתה בפועל. זו אינה בדיקת OOM או חומרה פיזית.
- **CI-004:** הושוו רשימות קלטי iOS push/PR, לרבות metadata/fixtures/dependencies; ריצה משולבת נדרשת לאימות build.

אין למזג שער מהותי נכשל. queued/in_progress הם מצב ריצה, לא חסם ולא PASS. מצב עדכני נקרא מ־[PR11](https://github.com/Sargon17-Green/consumer-law-reader/pull/11); [BACKLOG](BACKLOG.md) מפרט עבודה שנותרה, [EXTERNAL_ACTIONS](EXTERNAL_ACTIONS.md) מכיל רק חסמים חיצוניים אמיתיים. המקור המשפטי ותאריך אימותו לא שונו.
