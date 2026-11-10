# התאוששות מתהליך WebView שנעצר בפועל

ענף work/android-renderer-recovery-20261110 הוא בדיקה מבודדת ל־NATIVE-001/PERF-003, עם בסיס קוד706 וראיות QA פרטיות. אין שינוי בקוד המוצר.

אמולטורים API31/36 מתקינים Debug אמיתי ומנתקים רשת עם הוכחת connectivity. נשמרים גופן24 וסעיף14, מופעל API ציבורי WebViewRenderProcess.terminate(), ונדרשים חלון ההתאוששות של האפליקציה, לחיצה אמיתית על פתיחה מחדש, Activity/WebView חדשים ו־Ready אמיתי. נבדקים נתונים, עוגן ואינדקס חיפוש מקומי. בדיקה שאינה מצליחה לעצור renderer/להתאושש נכשלת; אין קריאה ישירה ל־onRenderProcessGone ואין טענת OOM פיזי.

מקורAndroid רשמי שנקרא10.11.2026: https://developer.android.com/reference/android/webkit/WebViewRenderProcess . API29+ מאפשר terminate; כשל בטיפול callback עלול לסיים גם את process האפליקציה. Android8 נבדק בתרחישים הרגילים ואינו מקבל PASS פיקטיבי ל־API שאינו קיים בו. אחרי אימות אפשר לשלב בדיקה זו ברגרסיה הכללית עם guard לגרסת המערכת.
