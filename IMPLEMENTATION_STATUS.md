# מצב מימוש, אימות ופרסום

נכון ל־10.11.2026. [קטלוג הדרישות](docs/requirements.json) הוא המקור המובנה; [PRODUCT_REQUIREMENTS](PRODUCT_REQUIREMENTS.md) נגזר ממנו. מימוש, אימות ופרסום נפרדים.

| ערוץ | ראיה שהסתיימה | פרסום |
|---|---|---|
| Web/PWA1.3.9-dev | source וארבעת הרוחבים על706a3bc עברו;47unit,32axe, כל66 התקנות ו־276יעדים בכל רוחב, ServiceWorker אמיתי ומטמון חסר זוהה | פורסם תיקון2/sourcec3e9d9e ב־reader/;75GET/SHA256 עברו כולל owner/alpha/APK. Pages42766006491 ופרסום42765882923 הסתיימו success |
| Android1.3.9-dev/code17 | כל שערי Linux/Android26/31/36 עברו על706a3bc. API36 שמר PDF146עמודים online וגם offline, אימות PdfRenderer/העדפות/חזרה ו־100מעברי ניווט. אבחון fresh portrait עם קריסת רכיב מערכת נותר בנפרד | אין חתימה חדשה במפתח המקורי; הציבורי1.3.5-beta נשמר |
| iOS1.3.9/build17 | על4ee85a3 ארבעת jobs עברו: iPhone26.2/iPad26.2/iPhone18.5/iPhone16.0. Native UI ו־Home Screen; archive מכשיר לא חתום | אין IPA חתום או TestFlight |

[Linux42721600913](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42721600913) נכשל כוללנית רק ב־API36; אין להציגו כ־PASS כולל. [iOS42721601016](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42721601016) הצליח כוללנית. מקורPR4ee85a379bcd9700125916133e1638a2fdd4f00a נבדק ב־merge-ref46d170c70555cdb637066bb6927601e747fc2800; לשניהם tree7578188ec14ef4421f70bcb177cd90c0fd698a22. [סיכום קבוע](qa/mobile-2026-11-08/acceptance-4ee85a3.json).

תיקוני NAV-006/PWA-001/CI-003 פורסמו ב־Web לאחר שעריו; Android ניווט עבר, iOS26.2 עבר ו־16/18.5 ממתינים. התיקונים כוללים: מוכנות מטמון לפי כל נכס נדרש והודעה למשתמש; יעדי תקנות מתחת לכפתור החזרה לאחר focus; אימות legacy Pages בקריאה בלבד. אין לייחס להם פרסום83fe או אימות Native ישן. בדיקת Print עודכנה להמתין לעמוד preview ממשי; קוד ההדפסה ומחזור החיים של המוצר לא שונו.

[אבחון PDF](qa/mobile-2026-11-08/android-print-preview-diagnosis.json) הוא ראיה מוגבלת, ולא קבלת Android מלאה. פרטי שיפורים ומטריצה: [הדוח ההנדסי](docs/MOBILE_ENGINEERING_2026-11-08_HE.md). מעבר ל־פורסם דורש bytes חיים/תוצר חתום, ומעבר ל־אומת דורש completed/log בתחום המוצהר.


קבלת [Linux706a3bc/run42764913617](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42764913617) הסתיימה success בכל9jobs; [סיכום קבוע](qa/mobile-2026-11-08/acceptance-706a3bc-linux.json). [HTTP תיקון2](qa/mobile-2026-11-08/public-web-patch-http-verification.json) ו־[תוצר פרסום](qa/mobile-2026-11-08/web-patch-candidate.json) הם הראיות לגרסה החיה האחרונה. הנתונים הישנים לעיל מתייחסים לקומיט4ee ואינם כשל חדש בקומיט706. iOS706 טרם הוכרע כוללנית; שני26.2jobs עברו,16/18.5 פעילים. אין PASS כולל לפני סיום.
