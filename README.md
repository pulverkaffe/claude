# Google Drive Duplicate Finder 🔍

Ett Python-verktyg för att hitta dubbletter i din Google Drive.

## Funktioner

- ✅ Hittar identiska filer baserat på MD5 checksum
- ✅ Hittar filer med samma namn
- ✅ Hittar filer med samma namn och storlek
- ✅ Visar bortkastet lagringsutrymme
- ✅ Visar direktlänkar till varje fil för enkel åtkomst

## Krav

- Python 3.7 eller senare
- Ett Google-konto med Google Drive
- Google Cloud Project med Drive API aktiverat

## Installation

### 1. Installera Python-beroenden

```bash
pip install -r requirements.txt
```

### 2. Konfigurera Google Drive API

För att använda detta verktyg behöver du en `credentials.json`-fil från Google Cloud Console:

1. Gå till [Google Cloud Console](https://console.cloud.google.com/)
2. Skapa ett nytt projekt eller välj ett befintligt
3. Aktivera Google Drive API:
   - Gå till "APIs & Services" > "Library"
   - Sök efter "Google Drive API"
   - Klicka på "Enable"
4. Skapa OAuth 2.0 credentials:
   - Gå till "APIs & Services" > "Credentials"
   - Klicka på "Create Credentials" > "OAuth client ID"
   - Välj "Desktop app" som application type
   - Ge den ett namn (t.ex. "Drive Duplicate Finder")
   - Klicka på "Create"
5. Ladda ner credentials:
   - Klicka på download-ikonen bredvid din nya OAuth 2.0 Client ID
   - Spara filen som `credentials.json` i samma mapp som skriptet

### 3. OAuth Consent Screen (om nödvändigt)

Om du inte redan har konfigurerat OAuth consent screen:

1. Gå till "APIs & Services" > "OAuth consent screen"
2. Välj "External" (om du inte har Google Workspace)
3. Fyll i nödvändig information:
   - App name: "Drive Duplicate Finder"
   - User support email: din email
   - Developer contact information: din email
4. Lägg till scopes:
   - Klicka på "Add or remove scopes"
   - Lägg till: `https://www.googleapis.com/auth/drive.readonly`
5. Lägg till testanvändare (dig själv) om appen är i testing mode

## Användning

Kör skriptet:

```bash
python find_drive_duplicates.py
```

### Första gången

Första gången du kör skriptet kommer det:
1. Öppna en webbläsare för inloggning
2. Be dig logga in på ditt Google-konto
3. Be om tillstånd att läsa dina Drive-filer (read-only)
4. Spara dina credentials i `token.pickle` för framtida användning

### Därefter

Vid efterföljande körningar använder skriptet den sparade `token.pickle`-filen och du behöver inte logga in igen.

## Output

Skriptet visar tre typer av dubletter:

### 1. Identiska Filer (MD5)
Filer med exakt samma innehåll, även om de har olika namn.

### 2. Filer med Samma Namn
Filer som har samma filnamn men kan ha olika innehåll.

### 3. Filer med Samma Namn och Storlek
Filer som har både samma namn och storlek (troligen dubbletter).

För varje dublett-grupp visas:
- Filnamn
- Fil-ID
- Storlek
- Skapelsedatum
- Ändringstid
- Direktlänk till filen

## Säkerhet

- Skriptet har **read-only** åtkomst till din Drive
- Det kan **inte** ta bort, ändra eller skapa filer
- `credentials.json` och `token.pickle` innehåller känslig information - dela dem inte
- Lägg till dessa filer i `.gitignore` om du använder versionshantering

## Filer

- `find_drive_duplicates.py` - Huvudskriptet
- `requirements.txt` - Python-beroenden
- `credentials.json` - Dina Google API credentials (skapas av dig)
- `token.pickle` - Sparade användar-tokens (skapas automatiskt)

## Felsökning

### "credentials.json saknas"
Du måste skapa OAuth credentials i Google Cloud Console (se steg 2 ovan).

### "Access denied" eller liknande fel
Kontrollera att:
1. Google Drive API är aktiverat i ditt projekt
2. Du har lagt till rätt scopes
3. Du har godkänt appen i OAuth consent screen

### Token utgången
Ta bort `token.pickle` och kör skriptet igen för att logga in på nytt.

## Licens

Fri att använda och modifiera för personligt bruk.
