# מצב מימוש, אימות ופרסום

נכון ל־10.11.2026. [קטלוג הדרישות](docs/requirements.json) הוא המקור המובנה; [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md) נגזר ממנו. מימוש, אימות ופרסום נפרדים.

| ערוץ | ראיה שהסתיימה | פרסום |
|---|---|---|
| Web/PWA1.3.9-dev | source וארבעת רוחבי הדפדפן על4ee85a3 עברו;32 סריקות axe ובדיקת ServiceWorker offline אמיתית | פורסם source83fe5ec ב־reader/;74 GET/SHA256 עברו כולל alpha ו־APK. Pages הרגיל42718136476 הסתיים success |
| Android1.3.9-dev/code17 | build ו־API26/31 online/offline על4ee85a3 עברו; API36 נכשל בשמירת PDF. בניסוי ממוקד e120c5d, המתנת preview אמיתי אפשרה PDF146עמודים במצב לרוחב; לאורך נכשל בתהליך עם קריסת רכיב מערכת | אין חתימה חדשה במפתח המקורי; הציבורי1.3.5-beta נשמר |
| iOS1.3.9/build17 | על4ee85a3 ארבעת jobs עברו: iPhone26.2/iPad26.2/iPhone18.5/iPhone16.0. Native UI ו־Home Screen; archive מכשיר לא חתום | אין IPA חתום או TestFlight |

[Linux42721600913](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42721600913) נכשל כוללנית רק ב־API36; אין להציגו כ־PASS כולל. [iOS42721601016](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42721601016) הצליח כוללנית. מקורPR4ee85a379bcd9700125916133e1638a2fdd4f00a נבדק ב־merge-ref46d170c70555cdb637066bb6927601e747fc2800; לשניהם tree7578188ec14ef4421f70bcb177cd90c0fd698a22. [סיכום קבוע](qa/mobile-2026-11-08/acceptance-4ee85a3.json).

תיקוני NAV-006/PWA-001/CI-003 במחזור הנוכחי ממומשים וממתינים לשערי CI ולפרסום נפרד: מוכנות מטמון לפי כל נכס נדרש והודעה למשתמש; יעדי תקנות מתחת לכפתור החזרה לאחר focus; אימות legacy Pages בקריאה בלבד. אין לייחס להם פרסום83fe או אימות Native ישן. בדיקת Print עודכנה להמתין לעמוד preview ממשי; קוד ההדפסה ומחזור החיים של המוצר לא שונו.

[אבחון PDF](qa/mobile-2026-11-08/android-print-preview-diagnosis.json) הוא ראיה מוגבלת, ולא קבלת Android מלאה. פרטי שיפורים ומטריצה: [הדוח ההנדסי](docs/MOBILE_ENGINEERING_2026-11-08_HE.md). מעבר ל־פורסם דורש bytes חיים/תוצר חתום, ומעבר ל־אומת דורש completed/log בתחום המוצהר.
