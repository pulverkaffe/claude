#!/usr/bin/env python3
"""
Beehiiv Import Script

Importerar markdown-filer från Google Drive till Beehiiv som drafts.
Filerna ska vara namngivna podd_X.md där X är ett nummer.

Användning:
    python import_to_beehiiv.py --dry-run          # Förhandsgranska
    python import_to_beehiiv.py                     # Skapa drafts
    python import_to_beehiiv.py --file "podd_5.md" # Enskild fil
"""

import os
import re
import json
import argparse
import pickle
import io
from typing import Optional, Tuple, List, Dict, Any

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Konstanter
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
BEEHIIV_API_BASE_URL = 'https://api.beehiiv.com/v2'
CONFIG_FILE = '.beehiiv_config.json'


class BeehiivImportError(Exception):
    """Basfel för Beehiiv-import"""
    pass


class ConfigurationError(BeehiivImportError):
    """Konfigurationsfel"""
    pass


class BeehiivAPIError(BeehiivImportError):
    """Fel vid kommunikation med Beehiiv API"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


def authenticate() -> Optional[Credentials]:
    """Autentisera med Google Drive API"""
    creds = None

    # Token filen lagrar användarens access och refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Om det inte finns några (giltiga) credentials, låt användaren logga in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("\n❌ Filen 'credentials.json' saknas!")
                print("\nFör att använda detta skript behöver du:")
                print("1. Gå till Google Cloud Console (https://console.cloud.google.com/)")
                print("2. Skapa ett nytt projekt eller välj ett befintligt")
                print("3. Aktivera Google Drive API")
                print("4. Skapa OAuth 2.0 credentials (Desktop app)")
                print("5. Ladda ner credentials.json och placera den i denna mapp")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Spara credentials för nästa körning
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def load_config(args: argparse.Namespace) -> Dict[str, str]:
    """
    Ladda konfiguration med prioritet: CLI > ENV > config file
    """
    config = {}

    # 1. Försök ladda från config-fil
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

    # 2. Överskrid med miljövariabler
    if os.getenv('BEEHIIV_API_KEY'):
        config['beehiiv_api_key'] = os.getenv('BEEHIIV_API_KEY')
    if os.getenv('BEEHIIV_PUBLICATION_ID'):
        config['beehiiv_publication_id'] = os.getenv('BEEHIIV_PUBLICATION_ID')
    if os.getenv('GOOGLE_DRIVE_FOLDER_ID'):
        config['google_drive_folder_id'] = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

    # 3. Överskrid med CLI-argument
    if args.folder_id:
        config['google_drive_folder_id'] = args.folder_id

    return config


def validate_config(config: Dict[str, str]) -> None:
    """Validera att alla nödvändiga konfigurationsvärden finns"""
    required = ['beehiiv_api_key', 'beehiiv_publication_id', 'google_drive_folder_id']
    missing = [key for key in required if not config.get(key)]

    if missing:
        raise ConfigurationError(
            f"Saknade konfigurationsvärden: {', '.join(missing)}\n"
            f"Ange dem i {CONFIG_FILE} eller som miljövariabler."
        )


def list_markdown_files(service: Any, folder_id: str) -> List[Dict[str, Any]]:
    """Hämta alla markdown-filer från en specifik mapp"""
    print(f"\n🔍 Söker efter podd_*.md filer i mappen...")

    files = []
    page_token = None

    try:
        while True:
            # Hämta filer från specifik mapp
            query = f"'{folder_id}' in parents and trashed=false and mimeType='text/markdown' or name contains '.md' and '{folder_id}' in parents and trashed=false"
            response = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token,
                pageSize=100
            ).execute()

            # Filtrera markdown-filer som matchar podd_X.md mönstret
            for file in response.get('files', []):
                if file['name'].endswith('.md'):
                    files.append(file)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        # Sortera efter filnamn
        files.sort(key=lambda f: f['name'])
        print(f"✅ Hittade {len(files)} markdown-filer")
        return files

    except HttpError as error:
        print(f'\n❌ Google Drive-fel: {error}')
        return []


def download_file_content(service: Any, file_id: str) -> Optional[str]:
    """Ladda ner innehållet från en Google Drive-fil"""
    try:
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        return content.decode('utf-8')
    except HttpError as error:
        print(f'❌ Kunde inte ladda ner fil: {error}')
        return None


def extract_episode_number(filename: str) -> Optional[int]:
    """
    Extrahera avsnittsnummer från filnamn.

    Exempel:
        podd_3.md -> 3
        podd_42.md -> 42
        invalid.md -> None
    """
    pattern = r'^podd_(\d+)\.md$'
    match = re.match(pattern, filename, re.IGNORECASE)

    if match:
        return int(match.group(1))
    return None


def extract_h1_title(content: str) -> Optional[str]:
    """
    Extrahera första H1-rubriken från markdown.

    Hanterar:
        # Enkel titel
        # Titel med **fetstil** och *kursiv*
    """
    pattern = r'^#\s+(.+?)$'

    for line in content.split('\n'):
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            title = match.group(1).strip()
            # Ta bort eventuell markdown-formatering från titeln
            title = re.sub(r'\*+', '', title)  # Ta bort ** och *
            title = re.sub(r'`', '', title)     # Ta bort backticks
            return title.strip()

    return None


def format_post_title(episode_num: int, h1_title: str) -> str:
    """
    Kombinera avsnittsnummer och H1-titel.

    Exempel:
        episode_num=4, h1_title="Meditation and mindfulness"
        -> "Podcast #4 – Meditation and mindfulness"
    """
    return f"Podcast #{episode_num} – {h1_title}"


def create_draft_post(config: Dict[str, str], title: str, content: str) -> Dict[str, Any]:
    """Skapa draft-inlägg i Beehiiv via API"""
    url = f"{BEEHIIV_API_BASE_URL}/publications/{config['beehiiv_publication_id']}/posts"

    headers = {
        'Authorization': f"Bearer {config['beehiiv_api_key']}",
        'Content-Type': 'application/json'
    }

    payload = {
        'title': title,
        'body_content': content,
        'status': 'draft',
        'audience': 'web',
        'content_tags': ['podcast']
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 401:
            raise BeehiivAPIError("Ogiltig API-nyckel", 401, response.text)
        elif response.status_code == 404:
            raise BeehiivAPIError("Publication hittades inte", 404, response.text)
        elif response.status_code == 429:
            raise BeehiivAPIError("Rate limit - vänta och försök igen", 429, response.text)
        else:
            raise BeehiivAPIError(
                f"API-anrop misslyckades: {response.text}",
                response.status_code,
                response.text
            )
    except requests.exceptions.Timeout:
        raise BeehiivAPIError("Timeout vid API-anrop", None, None)
    except requests.exceptions.ConnectionError:
        raise BeehiivAPIError("Kunde inte ansluta till Beehiiv", None, None)


def process_file(
    service: Any,
    file: Dict[str, Any],
    config: Dict[str, str],
    dry_run: bool
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Bearbeta en enskild fil.
    Returnerar (success, message, data)
    """
    filename = file['name']

    try:
        # 1. Validera filnamn
        episode_num = extract_episode_number(filename)
        if episode_num is None:
            return (False, f"⚠️  Matchar inte podd_X.md format", None)

        # 2. Ladda ner innehåll
        content = download_file_content(service, file['id'])
        if not content:
            return (False, f"❌ Kunde inte ladda ner filen", None)

        # 3. Extrahera H1
        h1_title = extract_h1_title(content)
        if not h1_title:
            return (False, f"⚠️  Ingen H1-rubrik hittades", None)

        # 4. Skapa titel
        post_title = format_post_title(episode_num, h1_title)

        # 5. Dry-run eller skapa post
        if dry_run:
            return (True, f"🔍 Skulle skapa: \"{post_title}\"", {'title': post_title})

        result = create_draft_post(config, post_title, content)
        post_id = result.get('data', {}).get('id', 'okänt')
        return (True, f"✅ Skapade draft: \"{post_title}\" (ID: {post_id})", result)

    except BeehiivAPIError as e:
        return (False, f"❌ Beehiiv API-fel: {e} (HTTP {e.status_code})", None)
    except Exception as e:
        return (False, f"❌ Oväntat fel: {e}", None)


def print_summary(results: List[Dict[str, Any]], dry_run: bool) -> None:
    """Skriv ut sammanfattning"""
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\n{'='*70}")
    print("SAMMANFATTNING" + (" (DRY RUN)" if dry_run else ""))
    print(f"{'='*70}")

    print(f"   ✅ {'Skulle skapa' if dry_run else 'Skapade'}: {len(successful)} drafts")
    print(f"   ⚠️  Hoppades över/fel: {len(failed)} filer")

    if failed:
        print(f"\n   Filer som inte bearbetades:")
        for r in failed:
            print(f"      - {r['file']}: {r['message']}")

    if dry_run and successful:
        print(f"\n💡 Kör utan --dry-run för att skapa drafts på riktigt")

    print(f"{'='*70}")


def parse_args() -> argparse.Namespace:
    """Parsa kommandoradsargument"""
    parser = argparse.ArgumentParser(
        description='Importera markdown-filer från Google Drive till Beehiiv som drafts'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Förhandsgranska utan att skapa drafts'
    )
    parser.add_argument(
        '--folder-id',
        type=str,
        help='Google Drive folder ID (överskriver config)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Bearbeta endast specifik fil'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Visa detaljerad utskrift'
    )
    return parser.parse_args()


def main():
    """Huvudfunktion"""
    print("=" * 70)
    print("📤 BEEHIIV IMPORT")
    print("=" * 70)

    args = parse_args()

    if args.dry_run:
        print("\n🔍 DRY-RUN MODE - Inga ändringar görs")

    # 1. Ladda och validera konfiguration
    try:
        config = load_config(args)
        validate_config(config)
    except ConfigurationError as e:
        print(f"\n❌ Konfigurationsfel: {e}")
        return

    # 2. Autentisera med Google Drive
    creds = authenticate()
    if not creds:
        return

    try:
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"\n❌ Kunde inte ansluta till Google Drive: {e}")
        return

    # 3. Hämta filer
    files = list_markdown_files(service, config['google_drive_folder_id'])

    if not files:
        print("\n❌ Inga markdown-filer hittades i mappen")
        return

    # 4. Filtrera om --file angetts
    if args.file:
        files = [f for f in files if f['name'] == args.file]
        if not files:
            print(f"\n❌ Filen '{args.file}' hittades inte")
            return

    print(f"\n📊 Bearbetar {len(files)} fil(er)...")

    # 5. Bearbeta filer
    results = []
    for i, file in enumerate(files, 1):
        print(f"\n   [{i}/{len(files)}] {file['name']}")
        success, message, data = process_file(service, file, config, args.dry_run)
        results.append({
            'file': file['name'],
            'success': success,
            'message': message,
            'data': data
        })
        print(f"         {message}")

    # 6. Skriv ut sammanfattning
    print_summary(results, args.dry_run)


if __name__ == '__main__':
    main()
