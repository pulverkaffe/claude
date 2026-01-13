# Detaljerad Guide: Skapa Google Cloud Projekt och Aktivera Drive API

Denna guide visar exakt hur du skapar ett Google Cloud-projekt och konfigurerar Google Drive API för att kunna använda duplicate finder-verktyget.

## Del 1: Skapa ett Google Cloud Projekt

### Steg 1: Gå till Google Cloud Console
1. Öppna din webbläsare och gå till: **https://console.cloud.google.com/**
2. Logga in med ditt Google-konto

### Steg 2: Skapa ett nytt projekt
1. Längst upp till vänster, bredvid "Google Cloud", klicka på **projekt-dropdown-menyn**
   - Här ser du eventuella befintliga projekt
2. Klicka på knappen **"NEW PROJECT"** (Nytt projekt) längst upp till höger i dialogen
3. Fyll i projektinformationen:
   - **Project name**: Skriv in t.ex. "Drive Duplicate Finder"
   - **Location**: Lämna som "No organization" (om du inte har en organisation)
4. Klicka på **"CREATE"** (Skapa)
5. Vänta några sekunder medan projektet skapas
6. Du kommer se en notifikation när projektet är klart - klicka på **"SELECT PROJECT"**

## Del 2: Aktivera Google Drive API

### Steg 3: Öppna API Library
1. I Google Cloud Console, klicka på **hamburger-menyn** (☰) längst upp till vänster
2. Navigera till: **APIs & services** → **Library**
   - Alternativt: **More products** → **Google Workspace** → **Product Library**
3. Du är nu i API Library där du kan söka efter och aktivera olika APIs

### Steg 4: Sök och aktivera Google Drive API
1. I sökfältet överst, skriv: **"Google Drive API"**
2. Klicka på **"Google Drive API"** i sökresultaten
   - Du kommer se en produktsida med information om API:et
3. Klicka på den stora blå knappen **"ENABLE"** (Aktivera)
4. Vänta några sekunder medan API:et aktiveras
5. När det är klart kommer du till API:ets dashboard-sida

## Del 3: Konfigurera OAuth Consent Screen

### Steg 5: Skapa OAuth Consent Screen
1. I menyn till vänster, klicka på **"OAuth consent screen"**
2. Välj **"External"** (om du inte har Google Workspace)
   - Detta gör att du kan använda API:et med vilket Google-konto som helst
3. Klicka på **"CREATE"**

### Steg 6: Fyll i App-information
1. **App information**:
   - **App name**: "Drive Duplicate Finder" (eller vad du vill)
   - **User support email**: Välj din egen email från dropdown
   - **App logo**: (Valfritt - kan lämnas tomt)

2. **App domain** (Valfritt - kan lämnas tomt för privat bruk):
   - Application home page: (kan lämnas tom)
   - Application privacy policy link: (kan lämnas tom)
   - Application terms of service link: (kan lämnas tom)

3. **Authorized domains**: (Kan lämnas tomt för privat bruk)

4. **Developer contact information**:
   - **Email addresses**: Ange din email

5. Klicka på **"SAVE AND CONTINUE"**

### Steg 7: Lägg till Scopes (Behörigheter)
1. Klicka på **"ADD OR REMOVE SCOPES"**
2. I sökfältet, skriv: **"drive.readonly"**
3. Markera checkboxen för: **".../auth/drive.readonly"**
   - Beskrivning: "See and download all your Google Drive files"
4. Klicka på **"UPDATE"** längst ner
5. Klicka på **"SAVE AND CONTINUE"**

### Steg 8: Lägg till testanvändare
1. Under "Test users", klicka på **"ADD USERS"**
2. Ange din egen email-adress (det Google-konto du ska använda)
3. Klicka på **"ADD"**
4. Klicka på **"SAVE AND CONTINUE"**

### Steg 9: Granska och slutför
1. Granska sammanfattningen
2. Klicka på **"BACK TO DASHBOARD"**

## Del 4: Skapa OAuth 2.0 Credentials

### Steg 10: Skapa credentials
1. I menyn till vänster, klicka på **"Credentials"**
2. Längst upp, klicka på **"+ CREATE CREDENTIALS"**
3. Välj **"OAuth client ID"** från dropdown-menyn

### Steg 11: Välj applikationstyp
1. **Application type**: Välj **"Desktop app"** från dropdown
2. **Name**: Skriv in t.ex. "Drive Duplicate Finder Desktop"
3. Klicka på **"CREATE"**

### Steg 12: Ladda ner credentials
1. En dialog visas: "OAuth client created"
2. Du ser ditt **Client ID** och **Client secret**
3. Klicka på **"DOWNLOAD JSON"** (Ladda ner JSON)
4. Spara filen - den heter något i stil med:
   `client_secret_XXXXX.apps.googleusercontent.com.json`

### Steg 13: Döp om filen
1. Gå till din nedladdningsmapp
2. Döp om den nedladdade filen till exakt: **`credentials.json`**
3. Flytta filen till samma mapp där `find_drive_duplicates.py` ligger:
   ```bash
   mv ~/Downloads/client_secret_*.json /home/user/claude/credentials.json
   ```

## Klart!

Nu har du:
✅ Skapat ett Google Cloud-projekt
✅ Aktiverat Google Drive API
✅ Konfigurerat OAuth Consent Screen
✅ Skapat och laddat ner credentials.json

Du kan nu köra skriptet:
```bash
cd /home/user/claude
python find_drive_duplicates.py
```

Vid första körningen kommer skriptet:
1. Öppna en webbläsare
2. Be dig logga in
3. Visa ett varningsmeddelande om att appen är "unverified" - klicka på "Advanced" → "Go to Drive Duplicate Finder (unsafe)"
4. Ge behörighet till read-only åtkomst till din Drive
5. Spara token för framtida användning

## Vanliga problem

### "The app is unverified"
Detta är normalt för appar i test-läge. Klicka på "Advanced" → "Go to [App name] (unsafe)" för att fortsätta.

### "Access blocked: This app's request is invalid"
Kontrollera att du har lagt till dig själv som testanvändare i OAuth consent screen.

### "Error 400: redirect_uri_mismatch"
Kontrollera att du valde "Desktop app" som Application type, inte "Web application".

## Säkerhetsnotering

- Skriptet har **read-only** åtkomst och kan inte ändra eller ta bort filer
- `credentials.json` innehåller känslig information - dela den inte
- `token.pickle` (skapas efter första körningen) innehåller också känslig information
