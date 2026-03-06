/**
 * Livestock Health Translation Utility
 * Provides functions for client-side translation
 */

class Translator {
    constructor() {
        // Get current language from data attribute or cookie
        this.currentLanguage = document.documentElement.lang || 
                              document.documentElement.getAttribute('data-language') || 
                              this.getCookie('language') || 
                              'en';
        
        // Check session storage for temporary language override (persists during session)
        const sessionLanguage = sessionStorage.getItem('temp_language');
        if (sessionLanguage) {
            this.currentLanguage = sessionLanguage;
        }
        
        console.log(`Translator initialized with language: ${this.currentLanguage}`);
    }
    
    /**
     * Get cookie value by name
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    /**
     * Translate text
     * @param {string} text - Text to translate
     * @param {string} targetLanguage - Target language (optional, defaults to current language)
     * @param {string} sourceLanguage - Source language (optional, defaults to 'en')
     * @returns {Promise} - Promise that resolves with the translated text
     */
    async translate(text, targetLanguage = null, sourceLanguage = 'en') {
        if (!text) return '';
        
        // Use current language if no target language specified
        targetLanguage = targetLanguage || this.currentLanguage;
        
        // Skip translation if target is same as source
        if (targetLanguage === sourceLanguage) {
            return text;
        }
        
        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    target_language: targetLanguage,
                    source_language: sourceLanguage
                })
            });
            
            if (!response.ok) {
                throw new Error(`Translation failed: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            return data.translated;
        } catch (error) {
            console.error('Translation error:', error);
            return text; // Return original text on error
        }
    }
    
    /**
     * Translate all elements with data-translate attribute
     */
    async translatePage() {
        const elements = document.querySelectorAll('[data-translate]');
        
        for (const element of elements) {
            const text = element.getAttribute('data-translate');
            
            try {
                const translated = await this.translate(text);
                element.textContent = translated;
            } catch (error) {
                console.error(`Error translating element: ${text}`, error);
            }
        }
        
        return true;
    }
    
    /**
     * Change the current language
     * @param {string} newLanguage - The new language code
     * @param {boolean} isPermanent - Whether to save the change permanently (default: false)
     */
    changeLanguage(newLanguage, isPermanent = false) {
        if (this.currentLanguage === newLanguage) return;
        
        if (isPermanent) {
            // Clear any temporary language override in session storage
            sessionStorage.removeItem('temp_language');
            
            // Create a form to submit language change to server (permanent change)
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/language/set';
            
            // Add language input
            const languageInput = document.createElement('input');
            languageInput.type = 'hidden';
            languageInput.name = 'language';
            languageInput.value = newLanguage;
            form.appendChild(languageInput);
            
            // Add next URL input
            const nextInput = document.createElement('input');
            nextInput.type = 'hidden';
            nextInput.name = 'next';
            nextInput.value = window.location.href;
            form.appendChild(nextInput);
            
            // Submit form
            document.body.appendChild(form);
            form.submit();
        } else {
            // Temporary language change for current page only
            console.log(`Changing language temporarily to: ${newLanguage}`);
            
            // Update current language
            const oldLanguage = this.currentLanguage;
            this.currentLanguage = newLanguage;
            
            // Store temporary language in session storage (persists across page refreshes during session)
            sessionStorage.setItem('temp_language', newLanguage);
            
            // Create a temporary cookie that expires when the browser is closed
            document.cookie = `temp_language=${newLanguage}; path=/`;
            
            // Update language indicators in UI
            document.querySelectorAll('.language-code').forEach(element => {
                element.textContent = newLanguage;
            });
            
            // Update language dropdown state
            this.updateLanguageDropdownState(newLanguage);
            
            // Translate all visible text on the page
            this.translateAllPageContent(oldLanguage);
        }
    }
    
    /**
     * Update the language dropdown UI to reflect the current language
     */
    updateLanguageDropdownState(language) {
        // Mark active language in dropdown
        document.querySelectorAll('.dropdown-item').forEach(item => {
            const langCode = item.querySelector('.language-code');
            if (!langCode) return;
            
            if (langCode.textContent === language) {
                item.classList.add('active');
                if (item.querySelector('.bi-check-circle-fill') === null) {
                    const icon = document.createElement('i');
                    icon.className = 'bi bi-check-circle-fill ms-2 text-success';
                    item.appendChild(icon);
                }
            } else {
                item.classList.remove('active');
                const icon = item.querySelector('.bi-check-circle-fill');
                if (icon) icon.remove();
            }
        });
        
        // Update main language indicators in navbar and footer
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        dropdownToggles.forEach(toggle => {
            const langCode = toggle.querySelector('.language-code');
            if (langCode) {
                langCode.textContent = language;
            }
            
            // Try to update the language name too if it exists
            const languageName = this.getLanguageName(language);
            const nameEl = toggle.childNodes[toggle.childNodes.length - 1];
            if (nameEl && nameEl.nodeType === Node.TEXT_NODE) {
                nameEl.textContent = ` ${languageName}`;
            }
        });
    }
    
    /**
     * Translate all content on the page from old language to new language
     * @param {string} sourceLanguage - Source language code
     */
    async translateAllPageContent(sourceLanguage) {
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'position-fixed top-0 start-0 w-100 bg-primary text-white text-center py-2';
        loadingIndicator.textContent = 'Translating page...';
        loadingIndicator.style.zIndex = '9999';
        document.body.appendChild(loadingIndicator);
        
        try {
            // Find all text nodes in the body
            const textNodes = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                {
                    acceptNode: function(node) {
                        // Skip script and style elements
                        if (node.parentNode.nodeName === 'SCRIPT' || 
                            node.parentNode.nodeName === 'STYLE' ||
                            node.parentNode.nodeName === 'NOSCRIPT') {
                            return NodeFilter.FILTER_REJECT;
                        }
                        // Accept non-empty text nodes
                        return node.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                    }
                }
            );
            
            while (walker.nextNode()) {
                textNodes.push(walker.currentNode);
            }
            
            // Batch translate text nodes
            const batchSize = 20;
            for (let i = 0; i < textNodes.length; i += batchSize) {
                const batch = textNodes.slice(i, i + batchSize);
                const texts = batch.map(node => node.textContent.trim());
                
                // Skip empty texts
                if (texts.every(t => !t)) continue;
                
                // Translate batch together
                const promises = texts.map(text => 
                    this.translate(text, this.currentLanguage, sourceLanguage)
                );
                
                const translations = await Promise.all(promises);
                
                // Apply translations
                for (let j = 0; j < batch.length; j++) {
                    if (translations[j] && texts[j]) {
                        batch[j].textContent = batch[j].textContent.replace(texts[j], translations[j]);
                    }
                }
            }
            
            // Translate placeholder attributes in input fields
            const inputElements = document.querySelectorAll('input[placeholder], textarea[placeholder]');
            for (const element of inputElements) {
                const placeholder = element.getAttribute('placeholder');
                if (placeholder && placeholder.trim()) {
                    const translated = await this.translate(placeholder, this.currentLanguage, sourceLanguage);
                    element.setAttribute('placeholder', translated);
                }
            }
            
            // Translate alt text in images
            const imageElements = document.querySelectorAll('img[alt]');
            for (const element of imageElements) {
                const alt = element.getAttribute('alt');
                if (alt && alt.trim()) {
                    const translated = await this.translate(alt, this.currentLanguage, sourceLanguage);
                    element.setAttribute('alt', translated);
                }
            }
            
        } catch (error) {
            console.error('Error translating page content:', error);
        } finally {
            // Remove loading indicator
            loadingIndicator.remove();
            
            // Show success message
            const successMsg = document.createElement('div');
            successMsg.className = 'position-fixed top-0 start-0 w-100 bg-success text-white text-center py-2';
            successMsg.textContent = `Page translated to ${this.getLanguageName(this.currentLanguage)}`;
            successMsg.style.zIndex = '9999';
            document.body.appendChild(successMsg);
            
            // Remove after 3 seconds
            setTimeout(() => {
                successMsg.remove();
            }, 3000);
        }
    }
    
    /**
     * Get language name from language code
     */
    getLanguageName(code) {
        const languages = {
            'en': 'English',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'bn': 'Bengali',
            'pa': 'Punjabi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam'
        };
        return languages[code] || code;
    }
    
    /**
     * Reset temporary language to user's preferred language
     */
    resetTemporaryLanguage() {
        sessionStorage.removeItem('temp_language');
        document.cookie = 'temp_language=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        window.location.reload();
    }
}

// Create global translator instance
window.translator = new Translator();

/**
 * Force a complete translation of the sidebar and navigation elements
 */
function forceCompletePageTranslation() {
    // Add data attribute to body to mark that complete translation has run
    if (document.body.hasAttribute('data-translation-complete')) {
        return;
    }

    console.log('Forcing complete page translation...');
    
    // Specifically target sidebar and navbar elements to ensure they get translated
    const sidebarLinks = document.querySelectorAll('.sidebar-link, .navbar .nav-link');
    const sidebarTexts = [];
    
    // Extract text content from sidebar links
    sidebarLinks.forEach(link => {
        // Skip links with no text content or language dropdown
        if (!link.textContent.trim() || link.closest('.language-dropdown')) {
            return;
        }
        
        // Save original text to translate
        const originalText = link.textContent.trim();
        sidebarTexts.push({ element: link, text: originalText });
    });
    
    // Skip if no sidebar links found
    if (sidebarTexts.length === 0) {
        return;
    }
    
    // Translate all sidebar texts
    Promise.all(
        sidebarTexts.map(item => window.translator.translate(item.text, window.translator.currentLanguage, 'en'))
    ).then(translations => {
        // Apply translations to sidebar elements
        sidebarTexts.forEach((item, index) => {
            if (translations[index]) {
                // Apply translation only to text nodes, preserving icon elements
                Array.from(item.element.childNodes).forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                        node.textContent = ' ' + translations[index].trim();
                    }
                });
            }
        });
        
        // Mark that complete translation has run
        document.body.setAttribute('data-translation-complete', 'true');
        console.log('Complete page translation finished');
    }).catch(error => {
        console.error('Error during complete page translation:', error);
    });
}

// Add event listener to translate page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.translator) {
        // Apply temporary language override if needed
        const tempLang = sessionStorage.getItem('temp_language');
        if (tempLang) {
            window.translator.updateLanguageDropdownState(tempLang);
        }
        
        // Translate page elements with data-translate attribute
        window.translator.translatePage();
        
        // Force complete translation of sidebar and navigation for users with database language
        // This helps when server-side translation might have missed some elements
        setTimeout(forceCompletePageTranslation, 500);
    }
}); 