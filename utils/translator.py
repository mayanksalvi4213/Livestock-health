"""
Google Cloud Translation API integration for livestock app
"""
import os
import requests
import html
import json
from flask import g, current_app
import traceback
import time

# Google API key for Translation API
GOOGLE_API_KEY = "AIzaSyBu2-A5dCNjUj53YtTd91bXsZC__az5WqM"

# Cache for translations to reduce API calls
translation_cache = {}

# Add time-based cache expiration (24 hours)
translation_cache_timestamp = {}
CACHE_EXPIRY = 86400  # 24 hours in seconds

# Supported languages
SUPPORTED_LANGUAGES = [
    'en',  # English
    'hi',  # Hindi
    'ta',  # Tamil
    'te',  # Telugu
    'mr',  # Marathi
    'bn',  # Bengali
    'pa',  # Punjabi
    'gu',  # Gujarati
    'kn',  # Kannada
    'ml',  # Malayalam
]

# Debug mode - set to True to print all translation requests
DEBUG_TRANSLATION = True

def translate_text(text, target_language, source_language='en'):
    """
    Translate text using Google Cloud Translation API
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code (e.g., 'hi' for Hindi)
        source_language (str): Source language code (default: 'en' for English)
    
    Returns:
        str: Translated text
    """
    if not text:
        print(f"[TRANSLATION] Empty text, skipping translation")
        return text
    
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        print(f"[TRANSLATION] Unsupported target language: {target_language}, defaulting to English")
        target_language = 'en'
    
    print(f"[TRANSLATION] Request to translate '{text[:30]}...' from {source_language} to {target_language}")
    
    # Return original text if target language is same as source
    if target_language == source_language:
        if DEBUG_TRANSLATION:
            print(f"[TRANSLATION] Skipping translation as target language ({target_language}) is same as source language ({source_language})")
        return text
    
    # Check cache first
    cache_key = f"{source_language}:{target_language}:{text}"
    current_time = time.time()
    
    # Check if we have a valid cached translation
    if cache_key in translation_cache:
        cache_time = translation_cache_timestamp.get(cache_key, 0)
        # Use cache if it's still valid (not expired)
        if current_time - cache_time < CACHE_EXPIRY:
            if DEBUG_TRANSLATION:
                print(f"[TRANSLATION] Cache hit: {cache_key[:50]}...")
            return translation_cache[cache_key]
        else:
            if DEBUG_TRANSLATION:
                print(f"[TRANSLATION] Cache expired: {cache_key[:50]}...")
    
    try:
        if DEBUG_TRANSLATION:
            print(f"[TRANSLATION] Translating from {source_language} to {target_language}: '{text[:50]}...'")
        
        # API endpoint for translation
        url = "https://translation.googleapis.com/language/translate/v2"
        
        # Parameters for the API request
        params = {
            'q': text,
            'target': target_language,
            'format': 'text',
            'key': GOOGLE_API_KEY
        }
        
        # Add source language if specified
        if source_language:
            params['source'] = source_language
            
        # Make the API request
        if DEBUG_TRANSLATION:
            print(f"[TRANSLATION] Making API request to {url}")
            
        response = requests.post(url, params=params)
        
        # If successful, extract the translated text
        if response.status_code == 200:
            data = response.json()
            
            if DEBUG_TRANSLATION:
                print(f"[TRANSLATION] API response: {data}")
                
            if 'data' in data and 'translations' in data['data'] and data['data']['translations']:
                translated_text = html.unescape(data['data']['translations'][0]['translatedText'])
                
                # Cache the translation with timestamp
                translation_cache[cache_key] = translated_text
                translation_cache_timestamp[cache_key] = current_time
                
                if DEBUG_TRANSLATION:
                    print(f"[TRANSLATION] Translated text: '{translated_text[:50]}...'")
                    
                return translated_text
            else:
                if DEBUG_TRANSLATION:
                    print(f"[TRANSLATION] API response does not contain translations: {data}")
                print(f"Translation API error: Invalid response format: {data}")
                return text
        
        # If there was an error, log it and return the original text
        if DEBUG_TRANSLATION:
            print(f"[TRANSLATION] API error: {response.status_code} - {response.text}")
            
        print(f"Translation API error: {response.status_code} - {response.text}")
        return text
        
    except Exception as e:
        print(f"Translation error: {str(e)}")
        if DEBUG_TRANSLATION:
            print(f"[TRANSLATION] Exception: {str(e)}")
            print(traceback.format_exc())
        return text

def batch_translate(texts, target_language, source_language='en'):
    """
    Translate multiple texts at once to reduce API calls
    
    Args:
        texts (list): List of texts to translate
        target_language (str): Target language code
        source_language (str): Source language code (default: 'en')
    
    Returns:
        list: List of translated texts in the same order
    """
    if not texts:
        return []
    
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        print(f"[TRANSLATION] Unsupported target language: {target_language}, defaulting to English")
        target_language = 'en'
        
    # Return original texts if target language is same as source
    if target_language == source_language:
        return texts
    
    # Filter out texts that are already in the cache
    texts_to_translate = []
    cached_indices = {}
    current_time = time.time()
    
    for i, text in enumerate(texts):
        cache_key = f"{source_language}:{target_language}:{text}"
        cache_time = translation_cache_timestamp.get(cache_key, 0)
        
        # Use cache if it's still valid (not expired)
        if cache_key in translation_cache and current_time - cache_time < CACHE_EXPIRY:
            cached_indices[i] = translation_cache[cache_key]
        else:
            texts_to_translate.append((i, text))
    
    # If all texts are cached, return them directly
    if not texts_to_translate:
        return [cached_indices[i] for i in range(len(texts))]
    
    try:
        # API endpoint for translation
        url = "https://translation.googleapis.com/language/translate/v2"
        
        # Parameters for the API request
        params = {
            'q': [text for _, text in texts_to_translate],
            'target': target_language,
            'format': 'text',
            'key': GOOGLE_API_KEY
        }
        
        # Add source language if specified
        if source_language:
            params['source'] = source_language
            
        # Make the API request
        response = requests.post(url, params=params)
        
        # If successful, extract the translated texts
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'translations' in data['data']:
                translations = data['data']['translations']
                
                # Create the result list with proper indices
                result = [None] * len(texts)
                
                # Fill in cached translations
                for i, trans in cached_indices.items():
                    result[i] = trans
                
                # Fill in new translations
                for (i, text), translation in zip(texts_to_translate, translations):
                    translated_text = html.unescape(translation['translatedText'])
                    
                    # Cache the translation with timestamp
                    cache_key = f"{source_language}:{target_language}:{text}"
                    translation_cache[cache_key] = translated_text
                    translation_cache_timestamp[cache_key] = current_time
                    
                    result[i] = translated_text
                
                return result
        
        # If there was an error, log it and return the original texts
        print(f"Batch translation API error: {response.status_code} - {response.text}")
        return [text for _, text in texts_to_translate]
        
    except Exception as e:
        print(f"Batch translation error: {str(e)}")
        print(traceback.format_exc())
        return [text for _, text in texts_to_translate]

def translate_dict(data, target_language, source_language='en'):
    """
    Recursively translate all string values in a dictionary or list
    
    Args:
        data: Dictionary or list containing strings to translate
        target_language (str): Target language code
        source_language (str): Source language code (default: 'en')
    
    Returns:
        dict/list: Copy of the original data with translated strings
    """
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        print(f"[TRANSLATION] Unsupported target language: {target_language}, defaulting to English")
        target_language = 'en'
        
    # Return original data if target language is same as source
    if target_language == source_language:
        return data
    
    if isinstance(data, str):
        return translate_text(data, target_language, source_language)
    elif isinstance(data, dict):
        return {k: translate_dict(v, target_language, source_language) for k, v in data.items()}
    elif isinstance(data, list):
        return [translate_dict(item, target_language, source_language) for item in data]
    else:
        return data
        
def clear_translation_cache():
    """Clear the translation cache"""
    global translation_cache, translation_cache_timestamp
    translation_cache = {}
    translation_cache_timestamp = {}
    print("[TRANSLATION] Cache cleared") 