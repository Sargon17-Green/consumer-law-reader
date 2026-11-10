# אבחון PDF עם ראיות פרטיות — IO-003

בסיס706a3bc; קבלת Android26/31/36 מלאה כבר עברה בריצה42764913617. הניסוי החדש מבודד fresh portrait/landscape; אין שינוי בקוד המוצר או lifecycle.

בכשל portrait של e120/run42726433709 הוכח רצף: MediaProvider/FuseDaemon pf_setattr קרס, StorageManager איפס את האחסון, vold רשם Killing all processes referencing /storage/emulated/0 ואז Sending Interrupt to pid2164 reader.consumer; reader יצא ב־SIGINT. זה מסביר את יציאת תהליך הבדיקה בלי חריגת Java באפליקציה. טריגר ה־MediaProvider עדיין אינו מוכח.

הבדיקה הקודמת כתבה צילומים/JSON ל־externalFiles והעתיקה PDF באמצעות shell cp לאותו FUSE. השערת הניסוי: פעולות ראיות הבדיקה מוסיפות גישות/שינוי metadata לאחסון המשותף, שאינן חלק מפעולת ההדפסה של המוצר. כעת רק פעולת Save as PDF האמיתית משתמשת ב־SAF/Downloads; העתק הראיה זורם כבתים תחומים32MB ל־files הפרטי של Debug app, בלי cp/setattr חיצוני. SHA256 ו־PdfRenderer נשארים חובה. ראיות נאספות ב־run-as של חבילת QA מורשית; אין הוספת הרשאות למוצר. אין לטעון שתוקן MediaProvider על סמך הצלחה יחידה.

שני הכיוונים חייבים לעבור עם PDF אמיתי וחזרה ל־reader. כשל נשאר כשל ומגובה בלוג/צילום. השינוי ייכנס ל־CI הכללי רק לאחר אימות; תוצרי סימולטור/Debug אינם שדרוג חתום.
