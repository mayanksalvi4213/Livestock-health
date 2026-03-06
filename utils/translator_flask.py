"""
Flask extension for automatic translation of content
"""
from functools import wraps
from flask import g, request, current_app, render_template, session
import json
from utils.translator import translate_text, translate_dict, SUPPORTED_LANGUAGES

class Translator:
    """Flask extension for automatic translation"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the extension with the app"""
        app.config.setdefault('DEFAULT_LANGUAGE', 'en')
        app.config.setdefault('SUPPORTED_LANGUAGES', SUPPORTED_LANGUAGES)
        
        # Register template filters
        app.jinja_env.filters['translate'] = self.translate_filter
        
        # Register global functions
        app.jinja_env.globals['get_language'] = self.get_current_language
        app.jinja_env.globals['supported_languages'] = self.get_supported_languages
        
        # Register context processor
        app.context_processor(self.inject_translate)
        
        # Store extension on app
        app.extensions['translator'] = self

    def get_current_language(self):
        """Get current language from g or session or default"""
        # First check g
        if hasattr(g, 'language'):
            return g.language
        
        # Next check session
        if 'language' in session:
            return session['language']
            
        # Finally check cookie or use default
        return request.cookies.get('language', self.app.config['DEFAULT_LANGUAGE'])
        
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.app.config['SUPPORTED_LANGUAGES']

    def translate_filter(self, text):
        """Jinja filter to translate text"""
        if not text:
            return text
            
        current_lang = self.get_current_language()
        return translate_text(text, current_lang)

    def inject_translate(self):
        """Context processor to inject translate function into templates"""
        def translate(text):
            if not text:
                return text
                
            current_lang = self.get_current_language()
            return translate_text(text, current_lang)
            
        return dict(translate=translate)

    def translate_response(self, response):
        """Translate API response JSON data"""
        # Check if this is a JSON response
        if response.mimetype != 'application/json':
            return response
            
        # Get current language
        current_lang = self.get_current_language()
        if current_lang == self.app.config['DEFAULT_LANGUAGE']:
            return response
            
        try:
            # Parse and translate the response data
            data = json.loads(response.get_data(as_text=True))
            translated_data = translate_dict(data, current_lang)
            
            # Replace the response data
            response.data = json.dumps(translated_data)
        except Exception as e:
            # Log error but don't fail if JSON parsing fails
            print(f"Error translating JSON response: {str(e)}")
        
        return response

def translate_blueprint(bp):
    """Decorator to automatically translate all routes in a blueprint"""
    original_route = bp.route
    
    @wraps(original_route)
    def translated_route(rule, **options):
        def decorator(f):
            @wraps(f)
            def translated_view(*args, **kwargs):
                result = f(*args, **kwargs)
                
                # If result is a tuple (response, status_code) or (response, status_code, headers)
                if isinstance(result, tuple):
                    response, *rest = result
                    if isinstance(response, dict):
                        # Translate dict response
                        current_lang = getattr(g, 'language', current_app.config['DEFAULT_LANGUAGE'])
                        if current_lang != current_app.config['DEFAULT_LANGUAGE']:
                            response = translate_dict(response, current_lang)
                    return (response, *rest)
                
                # If result is a dict (will be jsonified)
                elif isinstance(result, dict):
                    # Translate dict response
                    current_lang = getattr(g, 'language', current_app.config['DEFAULT_LANGUAGE'])
                    if current_lang != current_app.config['DEFAULT_LANGUAGE']:
                        result = translate_dict(result, current_lang)
                
                return result
            
            return original_route(rule, **options)(translated_view)
        return decorator
    
    # Replace the route method
    bp.route = translated_route
    
    return bp

def translate_template_response(template_name_or_list, **context):
    """
    Enhanced version of flask.render_template that translates template variables
    """
    current_lang = getattr(g, 'language', current_app.config['DEFAULT_LANGUAGE'])
    if current_lang != current_app.config['DEFAULT_LANGUAGE']:
        # Translate all string values in the context
        translated_context = {}
        for key, value in context.items():
            if isinstance(value, str):
                translated_context[key] = translate_text(value, current_lang)
            else:
                translated_context[key] = value
        context = translated_context
    
    return render_template(template_name_or_list, **context) 