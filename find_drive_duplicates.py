#!/usr/bin/env python3
"""
Google Drive Duplicate Finder

Detta skript hittar dubbletter i din Google Drive baserat på:
- Filnamn
- Filstorlek
- MD5 checksum (för identiska filer)
"""

import os
import pickle
from collections import defaultdict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Om du ändrar dessa SCOPES, ta bort filen token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
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

def list_all_files(service):
    """Hämta alla filer från Google Drive"""
    print("\n🔍 Hämtar filer från Google Drive...")

    files = []
    page_token = None

    try:
        while True:
            # Hämta filer (exkludera mappar och papperskorgen)
            response = service.files().list(
                q="trashed=false",
                spaces='drive',
                fields='nextPageToken, files(id, name, size, md5Checksum, mimeType, parents, createdTime, modifiedTime)',
                pageToken=page_token,
                pageSize=1000
            ).execute()

            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)

            print(f"  Hittade {len(files)} filer hittills...", end='\r')

            if page_token is None:
                break

        print(f"\n✓ Totalt hittade {len(files)} filer")
        return files

    except HttpError as error:
        print(f'\n❌ Ett fel uppstod: {error}')
        return []

def find_duplicates_by_name(files):
    """Hitta filer med samma namn"""
    name_dict = defaultdict(list)

    for file in files:
        # Skippa mappar
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        name_dict[file['name']].append(file)

    # Filtrera ut filer som har dubletter
    duplicates = {name: file_list for name, file_list in name_dict.items() if len(file_list) > 1}

    return duplicates

def find_duplicates_by_content(files):
    """Hitta filer med identiskt innehåll (baserat på MD5)"""
    md5_dict = defaultdict(list)

    for file in files:
        # Skippa mappar och filer utan MD5 (t.ex. Google Docs)
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        if 'md5Checksum' not in file:
            continue

        md5_dict[file['md5Checksum']].append(file)

    # Filtrera ut filer som har dubletter
    duplicates = {md5: file_list for md5, file_list in md5_dict.items() if len(file_list) > 1}

    return duplicates

def find_duplicates_by_size(files):
    """Hitta filer med samma storlek"""
    size_dict = defaultdict(list)

    for file in files:
        # Skippa mappar och filer utan storlek
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        if 'size' not in file:
            continue

        size_dict[file['size']].append(file)

    # Filtrera ut filer som har dubletter (och samma namn)
    duplicates = {}
    for size, file_list in size_dict.items():
        if len(file_list) > 1:
            # Gruppera efter namn också
            name_groups = defaultdict(list)
            for f in file_list:
                name_groups[f['name']].append(f)

            for name, same_name_files in name_groups.items():
                if len(same_name_files) > 1:
                    key = f"{size}_{name}"
                    duplicates[key] = same_name_files

    return duplicates

def format_size(size_bytes):
    """Formatera filstorlek till läsbar form"""
    if size_bytes is None:
        return "N/A"

    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "N/A"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def print_duplicates(duplicates, title):
    """Skriv ut dubletter i ett läsbart format"""
    if not duplicates:
        print(f"\n✓ {title}: Inga dubletter hittades!")
        return

    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")

    total_duplicates = sum(len(file_list) - 1 for file_list in duplicates.values())
    total_waste = 0

    for key, file_list in duplicates.items():
        print(f"\n📁 Dublett-grupp ({len(file_list)} filer):")

        # Beräkna bortkasterat utrymme
        if 'size' in file_list[0]:
            try:
                file_size = int(file_list[0]['size'])
                waste = file_size * (len(file_list) - 1)
                total_waste += waste
                print(f"   Bortkastet utrymme: {format_size(waste)}")
            except (ValueError, TypeError, KeyError):
                pass

        for i, file in enumerate(file_list, 1):
            size = format_size(file.get('size'))
            print(f"   {i}. {file['name']}")
            print(f"      ID: {file['id']}")
            print(f"      Storlek: {size}")
            print(f"      Skapad: {file.get('createdTime', 'N/A')}")
            print(f"      Ändrad: {file.get('modifiedTime', 'N/A')}")
            print(f"      Länk: https://drive.google.com/file/d/{file['id']}/view")

    print(f"\n{'='*80}")
    print(f"Sammanfattning:")
    print(f"  Antal dublett-grupper: {len(duplicates)}")
    print(f"  Totalt antal extra filer: {total_duplicates}")
    if total_waste > 0:
        print(f"  Totalt bortkastet utrymme: {format_size(total_waste)}")
    print(f"{'='*80}")

def main():
    """Huvudfunktion"""
    print("=" * 80)
    print("Google Drive Duplicate Finder")
    print("=" * 80)

    # Autentisera
    creds = authenticate()
    if not creds:
        return

    try:
        # Bygg Drive API service
        service = build('drive', 'v3', credentials=creds)

        # Hämta alla filer
        files = list_all_files(service)

        if not files:
            print("\n❌ Inga filer hittades eller kunde inte hämta filer")
            return

        # Hitta dubletter på olika sätt
        print("\n" + "="*80)
        print("Analyserar filer för dubletter...")
        print("="*80)

        # 1. Dubletter baserat på exakt innehåll (MD5)
        content_duplicates = find_duplicates_by_content(files)
        print_duplicates(content_duplicates, "🔍 IDENTISKA FILER (Samma MD5 checksum)")

        # 2. Dubletter baserat på namn
        name_duplicates = find_duplicates_by_name(files)
        print_duplicates(name_duplicates, "📝 FILER MED SAMMA NAMN")

        # 3. Dubletter baserat på storlek och namn
        size_duplicates = find_duplicates_by_size(files)
        print_duplicates(size_duplicates, "📊 FILER MED SAMMA NAMN OCH STORLEK")

    except HttpError as error:
        print(f'\n❌ Ett fel uppstod: {error}')

if __name__ == '__main__':
    main()
