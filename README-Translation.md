# Multilingual Support for Livestock Health

This document provides information about the multilingual support feature in the Livestock Health application.

## Supported Languages

The application supports the following languages:

- English (EN)
- Hindi (हिंदी - HI)
- Tamil (தமிழ் - TA)
- Telugu (తెలుగు - TE)
- Marathi (मराठी - MR)
- Bengali (বাংলা - BN)
- Punjabi (ਪੰਜਾਬੀ - PA)
- Gujarati (ગુજરાતી - GU)
- Kannada (ಕನ್ನಡ - KN)
- Malayalam (മലയാളം - ML)

## How It Works

The multilingual system uses a combination of:

1. **Pre-defined translations** - Common UI elements and static text are defined in dictionaries
2. **Dynamic translation** - Text that isn't pre-defined is automatically translated using Google Translate API

### User Language Selection

Users can select their preferred language in multiple ways:

1. On the language selection page (`/language`)
2. From the language dropdown in the navigation bar
3. From their profile settings

The language preference is stored in:
- Browser cookie (for non-logged in users)
- User profile in the database (for logged in users)
- Session (for consistent experience during the session)

### Adding Text to the Application

When adding new text to the application, you have two options:

1. **Use the translate filter in templates**:
   ```html
   <h1>{{ "Your text here" | translate }}</h1>
   ```

2. **Use the t dictionary in templates**:
   ```html
   <h1>{{ t.welcome }}</h1>
   ```
   
   This requires adding the text key to the `translations` dictionary in `app.py` for each supported language.

3. **For JavaScript or dynamic content**:
   Use the API endpoint `/api/translate` with a POST request:
   ```javascript
   fetch('/api/translate', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ text: 'Text to translate' })
   })
   .then(response => response.json())
   .then(data => console.log(data.translated));
   ```

### Adding a New Language

To add support for a new language:

1. Add the language code and name to the `AVAILABLE_LANGUAGES` dictionary in `routes/language.py`
2. The system will automatically handle the rest through Google Translate API

## Translation Storage and Caching

To optimize performance and reduce API calls:

1. Translations are cached in memory during runtime
2. The cache has an expiry time of 24 hours
3. For common UI elements, pre-defined translations are used (stored in `app.py`)

## Maintenance

### Translation Cache Management

To clear the translation cache:

```python
from utils.translator import clear_translation_cache

# Clear the cache
clear_translation_cache()
```

### Google Translate API Key

The application uses a Google Translate API key for dynamic translations. The key is stored in `utils/translator.py`. Make sure this key is valid and has sufficient quota for your application's needs.

To update the API key, modify the `GOOGLE_API_KEY` variable in `utils/translator.py`.

## Troubleshooting

### Translation Not Working

1. Check that the Google Translate API key is valid
2. Verify the language code is supported (check `SUPPORTED_LANGUAGES` in `utils/translator.py`)
3. Check server logs for any API errors

### Language Not Persisting

1. Ensure cookies are enabled in the user's browser
2. Check the user's language preference in the database
3. Verify session configuration in `app.py`

## Advanced Configuration

Additional configuration options can be set in `app.py`:

- `DEFAULT_LANGUAGE`: The default language if none is specified (default: 'en')
- `SUPPORTED_LANGUAGES`: List of supported language codes
- `TRANSLATION_CACHE_EXPIRY`: Time in seconds before cached translations expire

## Further Development

Ideas for further enhancement:

1. Add a translation management system for manual refinement of translations
2. Implement fallback chains for specialized translations
3. Develop language-specific content recommendations 