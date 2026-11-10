# התאוששות מתהליך WebView שנעצר בפועל

ענף work/android-renderer-recovery-20261110 הוא בדיקה מבודדת ל־NATIVE-001/PERF-003, עם בסיס קוד706 וראיות QA פרטיות. אין שינוי בקוד המוצר.

אמולטורים API31/36 מתקינים Debug אמיתי ומנתקים רשת עם הוכחת connectivity. נשמרים גופן24 וסעיף14, מופעל API ציבורי WebViewRenderProcess.terminate(), ונדרשים חלון ההתאוששות של האפליקציה, לחיצה אמיתית על פתיחה מחדש, Activity/WebView חדשים ו־Ready אמיתי. נבדקים נתונים, עוגן ואינדקס חיפוש מקומי. בדיקה שאינה מצליחה לעצור renderer/להתאושש נכשלת; אין קריאה ישירה ל־onRenderProcessGone ואין טענת OOM פיזי.

מקורAndroid רשמי שנקרא10.11.2026: https://developer.android.com/reference/android/webkit/WebViewRenderProcess . API29+ מאפשר terminate; כשל בטיפול callback עלול לסיים גם את process האפליקציה. Android8 נבדק בתרחישים הרגילים ואינו מקבל PASS פיקטיבי ל־API שאינו קיים בו. אחרי אימות אפשר לשלב בדיקה זו ברגרסיה הכללית עם guard לגרסת המערכת.


f393/run42771358394: בשתי הגרסאות Native התאושש ויצר Activity/WebView חדשים וגופן24 נשמר, אבל assertion על location.hash נכשל. זה אינו מוכיח אובדן מיקום: session restore משתמש ב־goTo(...,false,false) כדי לא לייצר היסטוריה כפולה. הניסוי הבא בודק actual currentArticle וסעיף שמור עם snapshot JSON/PNG, וקובע גם CSS24 לפני שמירת המצב כדי לא ליצור layout לא עקבי באופן מלאכותי. בנוסף run-as לא מורשה לחבילות ה־QA החתומות שאינן debuggable; פלט שגיאה בן58בתים נאסף במקוםPNG. האיסוף תוקן ל־ADB root של userdebug emulator אחרי בדיקות הפונקציה, עם SELinux enforcing, whitelist קבצים ואימותmagic/גודל/SHA. אין שינוי ל־debuggable/הרשאות של המוצר ואין טענת כשל מוצר מוכח מה־hash בלבד.
