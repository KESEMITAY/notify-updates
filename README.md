# 🦊 מדריך חיבור עדכוני גיטהאב לקבוצת הווצאפ (GitHub WhatsApp Notifier)

מערכת זו מאפשרת לכם לקבל עדכון קליל ומגניב בעברית יומיומית לקבוצת הווצאפ המשותפת שלכם בכל פעם שמישהו מכם מעלה קוד חדש לגיטהאב. העדכון יכלול את שם המפתח, רשימת השינויים שבוצעו, רשימת הקבצים שהשתנו, וסיכום קצר כדי למנוע התנגשויות (Merge Conflicts).

---

## 🛠️ שלב 1: הרשמה וחיבור ל-Green-API (ווצאפ)
השירות **Green-API** מאפשר לנו לשלוח הודעות ווצאפ דרך קוד בחינם (בתוכנית המפתחים החינמית).
1. היכנסו לאתר [green-api.com](https://green-api.com) והירשמו (Sign Up).
2. לאחר ההתחברות, צרו **Instance** חדש (במסלול ה-**Developer** החינמי).
3. היכנסו ל-Dashboard של ה-Instance שנוצר.
4. סרקו את קוד ה-QR שמופיע שם באמצעות אפליקציית הווצאפ שלכם בטלפון (הגדרות -> מכשירים מקושרים -> קשר מכשיר), בדיוק כמו שמתחברים ל-WhatsApp Web.
5. ודאו שהסטטוס של ה-Instance שלכם משתנה ל-**Authorized**.
6. העתיקו ושמרו בצד את הנתונים הבאים מתוך ה-Dashboard:
   * **idInstance** (למשל: `1101123456`)
   * **apiTokenInstance** (למשל: `45a8f7c9...`)

---

## 🔑 שלב 2: יצירת מפתח ל-Gemini API
הבוט משתמש ב-Gemini API כדי לקרוא את שינויי הקוד ולנסח הודעת סיכום קלילה בעברית.
1. היכנסו ל-[Google AI Studio](https://aistudio.google.com/).
2. התחברו עם חשבון הגוגל שלכם.
3. לחצו על **Get API key** בצד שמאל למעלה.
4. לחצו על **Create API key** וצרו מפתח חדש.
5. העתיקו ושמרו את ה-API Key שקיבלתם.

---

## 📱 שלב 3: מציאת ה-ID של קבוצת הווצאפ שלכם
כדי שהבוט ידע לאיזו קבוצה לשלוח את ההודעות, נשתמש בסקריפט העזר המקומי שיצרנו:
1. פתחו טרמינל בתיקייה הזו.
2. הריצו את הסקריפט:
   ```bash
   python setup_helper.py
   ```
3. הזינו את ה-`idInstance` וה-`apiTokenInstance` שלכם כאשר תתבקשו.
4. הסקריפט יציג לכם רשימה של כל קבוצות הווצאפ הפעילות שלכם עם ה-ID של כל קבוצה (מזהה שמסתיים ב-`@g.us`).
5. בחרו את מספר הקבוצה הרצויה מהרשימה, ואשרו שליחת הודעת בדיקה (`y`).
6. ודאו שהודעת הבדיקה הגיעה לקבוצה שלכם בווצאפ!
7. העתיקו ושמרו את ה-**Group ID** שהתקבל.

---

## 🔒 שלב 4: הגדרת סודות (Secrets) בגיטהאב
עלינו לשמור את המפתחות והקודים בצורה מאובטחת בגיטהאב כדי שהבוט יוכל להשתמש בהם בענן:
1. היכנסו לריפוזיטורי שלכם בגיטהאב: [athlete-poster-automation](https://github.com/KESEMITAY/athlete-poster-automation).
2. לחצו על לשונית **Settings** (הגדרות) למעלה.
3. בתפריט הצדדי, רדו ל-**Secrets and variables** ולחצו על **Actions**.
4. לחצו על הכפתור הירוק **New repository secret**.
5. הוסיפו את 4 הסודות הבאים (שימו לב להעתיק את השמות בדיוק כפי שהם):
   * שם: `GREEN_API_ID_INSTANCE` | ערך: ה-`idInstance` שלכם.
   * שם: `GREEN_API_TOKEN` | ערך: ה-`apiTokenInstance` שלכם.
   * שם: `GREEN_API_GROUP_ID` | ערך: מזהה הקבוצה שקיבלתם בשלב 3 (למשל `1234567890-111111@g.us`).
   * שם: `GEMINI_API_KEY` | ערך: מפתח ה-Gemini API שקיבלתם בשלב 2.

---

## 📁 שלב 5: העתקת הקבצים לפרויקט והפעלה
כדי שהבוט יתחיל לפעול, עליכם להעתיק את קובצי המערכת לתוך תיקיית הפרויקט שלכם (`athlete-poster-automation`):
1. העתיקו את הקובץ [notify.py](file:///c:/Users/kesem/OneDrive/Desktop/KESEMITAY/CODE%20PROJECTS/notify%20updates/notify.py) ישירות אל תיקיית השורש (Root) של הריפוזיטורי שלכם.
2. צרו בתוך תיקיית השורש של הפרויקט תיקייה בשם `.github` ובתוכה תיקייה בשם `workflows` (אם הן לא קיימות כבר).
3. העתיקו את הקובץ [notify_whatsapp.yml](file:///c:/Users/kesem/OneDrive/Desktop/KESEMITAY/CODE%20PROJECTS/notify%20updates/notify_whatsapp.yml) אל תוך התיקייה שנוצרה: `.github/workflows/notify_whatsapp.yml`.
4. בצעו Commit ו-Push לקבצים הללו לפרויקט בגיטהאב:
   ```bash
   git add notify.py .github/workflows/notify_whatsapp.yml
   git commit -m "Add WhatsApp commit notification bot"
   git push origin main
   ```

זהו! מהרגע הזה, בכל פעם שמישהו מכם יעלה קוד חדש לכל ענף (Branch) בריפוזיטורי, תקבלו תוך שניות בודדות הודעה מנוסחת היטב בווצאפ עם כל השינויים. 🎉
