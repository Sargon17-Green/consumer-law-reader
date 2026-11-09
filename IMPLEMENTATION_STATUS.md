# מצב מימוש, אימות ופרסום

נכון למחזור 10.11.2026; יש לרענן מ־GitHub לפני פעולה. מצב כל דרישה נמצא ב־[docs/requirements.json](docs/requirements.json) ובתצוגה [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md). אין להסיק פרסום מהשלמת קוד.

| ערוץ | מימוש/אימות | פרסום |
|---|---|---|
| Web/PWA 1.3.9-dev (בטא) | source וארבעה browser jobs עברו ב־2f91d12; 32 סריקות axe; רוחב/חיפוש/גיבוי/היסטוריה | **פורסם** ב־reader/ מתוך source83fe5ec. אימות HTTP עבר לכל74 הקבצים, כולל alpha ו־APK, ב־10.11.2026; ראיה ב־qa/mobile-2026-11-08/public-web-http-verification.json |
| Android1.3.9-dev/code17 | build Debug + unsigned APK/AAB עברו; API31 online/offline עבר; API26 עבר בענף אבחון לאחר תיקון פעולת בדיקה; API36 עדיין דורש קבלת PDF/sharesheet | אין APK חדש חתום במפתח ההפצה; הציבורי נשאר1.3.5-beta |
| iOS1.3.9/build17 | ארבע משימות הסימולטור הסתיימו בהצלחה: iPhone26.2/iPad26.2/iPhone18.5/iPhone16.0; גם אייקון Home Screen; device archive לא חתום במסלול CI | אין IPA חתום, TestFlight או App Store שנבדקו |

ראיות: [Linux42683016176](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016176) נכשל כוללנית בשני תרחישי Native; אין להציגו כריצה ירוקה. source+4browser+build+API31 הצליחו. [iOS42683016332](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42683016332) הצליח כוללנית. [אבחון42685860051](https://github.com/Sargon17-Green/consumer-law-reader/actions/runs/42685860051) עבר API26 ונכשל API36 בבחירת יעד sharesheet; תוצרי בדיקה בלבד.

PR head2f91d12787f37a8b75d33e3f60d8813c6ecd081d; checkout הבדיקות היה merge commit d178bb6d1765707732e9ad8f5ed448a1de5ebac3, עם tree זהה cadba5f98945b5b122f87ffcecd1455a63f9d2f1. GitHub merge-ref אינו commit הפצה; התוצרים נושאים sourceCommit/tree מדויקים.

פרטי שיפורים, קבצים/בדיקות/commits ומטריצת יכולות: [הדוח ההנדסי](docs/MOBILE_ENGINEERING_2026-11-08_HE.md). תוצאות מסך וביצועים: `qa/mobile-2026-11-08/`. מעבר pending ל־PASS מותר רק לפי job completed/log/artifact, ומעבר ל־פורסם דורש בדיקת כתובת חיה או חתימה ותוצר הפצה.
