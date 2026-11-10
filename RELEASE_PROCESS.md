# בנייה, חתימה, פרסום ושדרוג

מפרסמים כל ערוץ שעבר שערי קבלה בנפרד. אין לדרוש השלמת Native כדי לפרסם Web, ואין להחליש שער בטיחות כדי להקדים מהדורה. תיעוד מצב מהדורות: RELEASE_HISTORY; פעולות חיצוניות: EXTERNAL_ACTIONS.

## Web/PWA

1. בוחרים commit נבדק ושומרים SHA/tree וראיות source/DOM/browser/offline. אין שינוי משפטי.
2. מריצים `scripts/build_web.py`, `verify_release.py`, בדיקות public_reader/reader_site, ומכינים באמצעות `prepare_reader_site.py` רק reader/ על גבי gh-pages הקיים. `.consumer-law-reader-owner.json` מזהה בעלות, commit וגיבובי38 הנכסים. אין להחליף תיקייה שאינה בבעלות התהליך.
3. `deploy_web.yml` שומר את קובצי alpha מחוץ ל־reader/ ללא שינוי, ואת public downloads/latest.apk. אין force-push או שינוי הגדרת Pages. סביבת github-pages מתירה main ו־gh-pages בלבד; אין להסיר או לעקוף את ההגנה.
4. לפי mode legacy מפורסם ענף gh-pages הקיים; לפי workflow משתמשים ב־Actions Pages הרשמיים. workflow עבודה עשוי להיכשל ב־environment אף לאחר שפרסום gh-pages האוטומטי השלים: אין להכריז שה־workflow עבר; מאמתים בנפרד run/HTTP ובתים של האתר החי.
5. `verify_public_reader.py verify` משווה את כל נכסי Web, marker, alpha ו־APK מול הציפיות שנשמרו לפני הפרסום; רק אז מעדכנים סטטוס ל־פורסם. הוראות Home Screen מבהירות שזה Web/PWA, לא IPA.

## Android

```bash
python scripts/fetch_tools.py
python scripts/build_android.py --debug
python scripts/build_android_qa.py
python scripts/build_android.py --unsigned
python scripts/build_android_bundle.py
```

Debug נחתם במפתח QA זמני ואינו משדרג את הציבורי. unsigned APK מיושר ו־AAB שסיומו UNSIGNED_NOT_FOR_UPLOAD נדרשים לחתימה מקורית; bundletool1.18.3 ודיגסטו מקובעים. משווים payload/code/assets, משאבי proto ממיקומים שונים, גיבוב ומספרי גרסה. ב־API36 מתקינים את ה־universal APK שנוצר מה־AAB.

להפצה חתומה, `scripts/build_android.py` ללא debug/unsigned דורש את **המפתח המקורי** בתיקיית signing/ המוחרגת מ־Git, alias law-reader. אין ליצור מפתח חלופי. מאמתים apksigner/zipalign, תעודת SHA256 ההיסטורית2625ebe860cb0bfac105196b24aeedf3a948ce18c6f836478fd8ea38d0b937dc, מקור חבילה, חתימה ושדרוג בלי מחיקת אפליקציה. רק לאחר מכן מפרסמים נכס Consumer_Law_Reader_*_Android.apk ב־Release חדש. אין שינוי tag ישן; sync_latest_download מקבל רק Release ציבורי וחתימה נכונה, ומעדכן downloads/latest.apk/latest.json. הקישור הציבורי1.3.5 אינו מוחלף לפני מועמד תואם.

## iOS/iPadOS

`ios/project.yml` הוא מקור ההגדרות; assets נוצרים ב־prepare_assets.sh, והפרויקט ב־XcodeGen. CI בונה סימולטורים ו־device archive לא חתום לאחר מבחני UIKit/WK/UI. למסלול חתימה משתמשים ב־`ios/scripts/archive_for_testflight.sh` עם APPLE_TEAM_ID ו־IOS_BUNDLE_ID מתוך חשבון מורשה בלבד. הפירוט ב־IOS_TESTFLIGHT_HE.md. אין לייחס קיומו של archive ל־IPA להפצה, TestFlight או אישור Apple.

בכל שחרור: גרסה/build תואמים; בדיקות מתייחסות ל־sourceCommit/tree של התוצר; מעדכנים requirements/status/history/known issues/handoff וראיות. לא מתקינים כלים במחשב המשתמש כאשר אפשר CI. אין תשלום או קבלת תנאים בשם המשתמש.
