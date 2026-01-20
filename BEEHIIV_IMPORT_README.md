# beehiiv Import Script 🐝

A Python script to bulk import Markdown files as draft posts into beehiiv.

## Features

- ✅ Imports Markdown files with front matter support
- ✅ Converts Markdown to HTML automatically
- ✅ Creates posts as drafts in beehiiv
- ✅ Supports custom metadata (title, subtitle, tags)
- ✅ Tracks imported posts to avoid duplicates
- ✅ Handles rate limiting automatically
- ✅ Dry-run mode to preview before importing
- ✅ Progress tracking and error handling

## Prerequisites

- Python 3.7 or later
- A beehiiv account
- beehiiv API access (see Setup section)

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up beehiiv API Access

Before you can use this script, you need to get your API credentials from beehiiv:

#### Get Your API Key

1. Log in to your beehiiv account
2. Go to **Settings** in the left panel
3. Scroll down to **Workspace Settings** and click **API**
4. Click **Create New API Key**
5. Give it a name (e.g., "Import Script")
6. **Important**: Copy the API key immediately - you won't be able to see it again!

#### Get Your Publication ID

1. In the same API settings page, scroll down to **Publication ID**
2. Select your publication
3. Copy the Publication ID shown

**Note**: You must be a workspace Owner or Admin to access API settings. You may also need to complete Stripe Identity Verification first.

### 3. Configure Environment Variables

Create a `.env` file in the same directory as the script:

```bash
cp .env.example .env
```

Then edit `.env` and add your credentials:

```env
BEEHIIV_API_KEY=your_api_key_here
BEEHIIV_PUBLICATION_ID=your_publication_id_here
POSTS_DIRECTORY=./posts
DRY_RUN=false
DELAY_BETWEEN_POSTS=2
```

### 4. Prepare Your Posts

Create a `posts` directory (or use the path you specified in `POSTS_DIRECTORY`) and add your Markdown files:

```bash
mkdir posts
```

## Markdown File Format

Your Markdown files can include optional front matter for metadata:

```markdown
---
title: My Amazing Post Title
subtitle: A compelling subtitle
content_tags: ["technology", "tutorial"]
---

# Your Post Content

Write your post content here in Markdown format.

- It supports **bold** and *italic*
- Lists and links
- Code blocks
- And more!
```

**If no front matter is provided**, the script will use the filename as the title.

### Supported Front Matter Fields

- `title`: Post title (required, or uses filename)
- `subtitle`: Optional subtitle
- `content_tags`: Array of tags

## Usage

### Test Run (Dry Run)

Before importing, do a test run to see what would be imported:

```bash
# Set DRY_RUN=true in .env, or:
DRY_RUN=true python beehiiv_import.py
```

### Import Posts

When you're ready, run the script:

```bash
python beehiiv_import.py
```

### What Happens

1. The script reads all `.md` and `.markdown` files from your posts directory
2. Parses each file and extracts metadata and content
3. Converts Markdown content to HTML
4. Creates each post as a **draft** in beehiiv
5. Saves an import log to track what's been imported
6. Waits between requests to respect rate limits

## Configuration Options

Edit these in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `BEEHIIV_API_KEY` | Your beehiiv API key | Required |
| `BEEHIIV_PUBLICATION_ID` | Your publication ID | Required |
| `POSTS_DIRECTORY` | Directory containing your Markdown files | `./posts` |
| `DRY_RUN` | Set to `true` to test without creating posts | `false` |
| `DELAY_BETWEEN_POSTS` | Seconds to wait between API calls | `2` |

## Import Log

The script creates an `import_log.json` file to track:

- Successfully imported posts (with post IDs and timestamps)
- Failed imports (with error details)

This prevents duplicate imports if you run the script multiple times.

### Reset Import Log

To re-import files, delete or rename the import log:

```bash
rm import_log.json
```

## Troubleshooting

### "BEEHIIV_API_KEY not set in environment"

Make sure you've created a `.env` file with your API key. See step 3 in Installation.

### "Posts directory not found"

Create the directory specified in `POSTS_DIRECTORY`:

```bash
mkdir posts
```

### "Failed to create post: 401"

Your API key is invalid or expired. Generate a new one in beehiiv settings.

### "Failed to create post: 403"

You may not have Enterprise access. The beehiiv API is currently only available to Enterprise users.

### "Failed to create post: 429"

Rate limit hit. The script will automatically wait and retry. You can increase `DELAY_BETWEEN_POSTS` in `.env` to slow down requests.

### Rate Limits

The script includes automatic rate limit handling. If you hit the rate limit:

- The script will wait 60 seconds before retrying
- You can adjust `DELAY_BETWEEN_POSTS` to add more delay between requests
- For large imports (100+ posts), consider running in batches

## Example Workflow

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your .env file with API credentials
cp .env.example .env
nano .env

# 3. Add your Markdown files to the posts directory
mkdir posts
cp ~/my-blog-posts/*.md posts/

# 4. Do a test run
DRY_RUN=true python beehiiv_import.py

# 5. Import for real
python beehiiv_import.py

# 6. Check your beehiiv dashboard for the draft posts!
```

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- The API key has full access to your beehiiv account - treat it like a password
- Add `.env` and `import_log.json` to your `.gitignore`

## Limitations

- The beehiiv API is currently in beta and only available to Enterprise users
- All posts are created as drafts (you'll need to publish them manually in beehiiv)
- The script converts Markdown to HTML - complex formatting may need adjustment
- Images must be hosted externally (use full URLs in your Markdown)

## Files

- `beehiiv_import.py` - Main import script
- `requirements.txt` - Python dependencies
- `.env` - Your configuration (create this)
- `.env.example` - Example configuration file
- `import_log.json` - Import tracking log (created automatically)

## Support

For issues with:
- **This script**: Check the error messages and troubleshooting section above
- **beehiiv API**: See [beehiiv API documentation](https://developers.beehiiv.com/)
- **API access**: Contact beehiiv support or check [their help center](https://www.beehiiv.com/support)

## Sources

This script was built using the beehiiv API documentation:
- [Create post API endpoint](https://developers.beehiiv.com/api-reference/posts/create)
- [Getting started with beehiiv API](https://developers.beehiiv.com/welcome/getting-started)
- [How to access API keys](https://www.beehiiv.com/support/article/13091918395799-how-to-access-your-publication-id-or-api-keys)

## License

Free to use and modify for personal use.
