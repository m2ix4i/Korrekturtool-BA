/**
 * Theme Manager Module
 * Handles light/dark theme switching with system preference detection
 * and persistent user preferences
 */

export class ThemeManager {
    constructor() {
        this.themes = {
            LIGHT: 'light',
            DARK: 'dark',
            AUTO: 'auto'
        };
        
        // Define theme cycle order
        this.themeOrder = [this.themes.AUTO, this.themes.LIGHT, this.themes.DARK];
        
        this.currentTheme = this.themes.AUTO;
        this.systemPreference = null;
        this.storageKey = 'korrekturtool-theme-preference';
        
        this.themeToggle = null;
        this.mediaQuery = null;
        
        this.init();
    }
    
    /**
     * Initialize the theme manager
     */
    init() {
        this.setupMediaQuery();
        this.loadSavedTheme();
        this.setupThemeToggle();
        this.applyTheme();
        this.setupKeyboardShortcuts();
        
        console.log('🎨 Theme Manager initialized');
    }
    
    /**
     * Setup media query listener for system preference changes
     */
    setupMediaQuery() {
        this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        this.systemPreference = this.mediaQuery.matches ? this.themes.DARK : this.themes.LIGHT;
        
        // Listen for system preference changes
        this.mediaQuery.addEventListener('change', (e) => {
            this.systemPreference = e.matches ? this.themes.DARK : this.themes.LIGHT;
            
            // If user is on auto theme, update immediately
            if (this.currentTheme === this.themes.AUTO) {
                this.applyTheme();
                this.announceThemeChange(`Automatisch zu ${this.getEffectiveTheme() === this.themes.DARK ? 'dunklem' : 'hellem'} Theme gewechselt`);
            }
        });
    }
    
    /**
     * Load saved theme preference from localStorage
     */
    loadSavedTheme() {
        try {
            const savedTheme = localStorage.getItem(this.storageKey);
            if (savedTheme && Object.values(this.themes).includes(savedTheme)) {
                this.currentTheme = savedTheme;
            }
        } catch (error) {
            console.warn('Fehler beim Laden der Theme-Einstellung:', error);
            // Fallback to auto theme
            this.currentTheme = this.themes.AUTO;
        }
    }
    
    /**
     * Save theme preference to localStorage
     */
    saveThemePreference() {
        try {
            localStorage.setItem(this.storageKey, this.currentTheme);
        } catch (error) {
            console.warn('Fehler beim Speichern der Theme-Einstellung:', error);
        }
    }
    
    /**
     * Setup theme toggle button
     */
    setupThemeToggle() {
        this.themeToggle = document.querySelector('.theme-toggle');
        
        if (!this.themeToggle) {
            console.warn('Theme-Toggle-Button nicht gefunden');
            return;
        }
        
        // Add click event listener
        this.themeToggle.addEventListener('click', () => {
            this.cycleTheme();
        });
        
        // Add keyboard event listener for Enter and Space
        this.themeToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.cycleTheme();
            }
        });
        
        // Update button attributes
        this.updateToggleButton();
    }
    
    /**
     * Setup keyboard shortcuts for theme switching
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + T for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.cycleTheme();
            }
        });
    }
    
    /**
     * Cycle through themes: auto -> light -> dark -> auto
     */
    cycleTheme() {
        const currentIndex = this.themeOrder.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % this.themeOrder.length;
        const nextTheme = this.themeOrder[nextIndex];
        
        this.setTheme(nextTheme);
    }
    
    /**
     * Set specific theme
     * @param {string} theme - Theme to set
     */
    setTheme(theme) {
        if (!Object.values(this.themes).includes(theme)) {
            console.warn(`Unbekanntes Theme: ${theme}`);
            return;
        }
        
        const previousTheme = this.currentTheme;
        this.currentTheme = theme;
        
        this.applyTheme();
        this.saveThemePreference();
        this.updateToggleButton();
        
        // Announce theme change
        const themeNames = {
            [this.themes.AUTO]: 'automatisches',
            [this.themes.LIGHT]: 'helles',
            [this.themes.DARK]: 'dunkles'
        };
        
        if (previousTheme !== theme) {
            this.announceThemeChange(`${themeNames[theme]} Theme aktiviert`);
        }
        
        // Dispatch custom event for other components
        this.dispatchThemeChangeEvent(previousTheme, theme);
    }
    
    /**
     * Apply the current theme to the document
     */
    applyTheme() {
        const effectiveTheme = this.getEffectiveTheme();
        
        // Remove any existing theme data attributes
        document.documentElement.removeAttribute('data-theme');
        
        // Apply theme data attribute (only for explicit themes)
        if (this.currentTheme !== this.themes.AUTO) {
            document.documentElement.setAttribute('data-theme', effectiveTheme);
        }
        
        // Update meta theme-color
        this.updateMetaThemeColor(effectiveTheme);
        
        // Add transition class for smooth theme changes
        document.body.classList.add('theme-transitioning');
        
        // Remove transition class after animation completes
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 300);
    }
    
    /**
     * Get the effective theme (resolves auto theme)
     * @returns {string} Effective theme
     */
    getEffectiveTheme() {
        if (this.currentTheme === this.themes.AUTO) {
            return this.systemPreference || this.themes.LIGHT;
        }
        return this.currentTheme;
    }
    
    /**
     * Update meta theme-color for browser UI
     * @param {string} theme - Current effective theme
     */
    updateMetaThemeColor(theme) {
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            const color = theme === this.themes.DARK ? '#0a84ff' : '#007aff';
            metaThemeColor.setAttribute('content', color);
        }
    }
    
    /**
     * Update theme toggle button state
     */
    updateToggleButton() {
        if (!this.themeToggle) return;
        
        const effectiveTheme = this.getEffectiveTheme();
        const icon = this.themeToggle.querySelector('.theme-toggle-icon');
        
        if (icon) {
            // Update icon based on current theme
            const icons = {
                [this.themes.AUTO]: '🌓',
                [this.themes.LIGHT]: '🌙',
                [this.themes.DARK]: '☀️'
            };
            
            icon.textContent = icons[this.currentTheme] || icons[this.themes.AUTO];
        }
        
        // Update ARIA label
        const labels = {
            [this.themes.AUTO]: 'Zu hellem Theme wechseln',
            [this.themes.LIGHT]: 'Zu dunklem Theme wechseln',
            [this.themes.DARK]: 'Zu automatischem Theme wechseln'
        };
        
        this.themeToggle.setAttribute('aria-label', labels[this.currentTheme]);
        
        // Update title
        const titles = {
            [this.themes.AUTO]: 'Automatisches Theme (folgt Systemeinstellung)',
            [this.themes.LIGHT]: 'Helles Theme',
            [this.themes.DARK]: 'Dunkles Theme'
        };
        
        this.themeToggle.setAttribute('title', titles[this.currentTheme]);
    }
    
    /**
     * Announce theme change to screen readers
     * @param {string} message - Message to announce
     */
    announceThemeChange(message) {
        const liveRegion = document.getElementById('ariaLivePolite');
        if (liveRegion) {
            liveRegion.textContent = message;
            
            // Clear the message after a short delay
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }
    
    /**
     * Dispatch custom theme change event
     * @param {string} previousTheme - Previous theme
     * @param {string} newTheme - New theme
     */
    dispatchThemeChangeEvent(previousTheme, newTheme) {
        const event = new CustomEvent('themechange', {
            detail: {
                previousTheme,
                newTheme,
                effectiveTheme: this.getEffectiveTheme()
            }
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * Get current theme information
     * @returns {Object} Theme information
     */
    getThemeInfo() {
        return {
            current: this.currentTheme,
            effective: this.getEffectiveTheme(),
            system: this.systemPreference,
            available: Object.values(this.themes)
        };
    }
    
    /**
     * Check if dark theme is active
     * @returns {boolean} True if dark theme is active
     */
    isDarkTheme() {
        return this.getEffectiveTheme() === this.themes.DARK;
    }
    
    /**
     * Check if light theme is active
     * @returns {boolean} True if light theme is active
     */
    isLightTheme() {
        return this.getEffectiveTheme() === this.themes.LIGHT;
    }
    
    /**
     * Check if auto theme is active
     * @returns {boolean} True if auto theme is active
     */
    isAutoTheme() {
        return this.currentTheme === this.themes.AUTO;
    }
    
    /**
     * Reset theme to system default
     */
    resetToSystemDefault() {
        this.setTheme(this.themes.AUTO);
    }
    
    /**
     * Add theme change listener
     * @param {Function} callback - Callback function
     */
    onThemeChange(callback) {
        document.addEventListener('themechange', callback);
    }
    
    /**
     * Remove theme change listener
     * @param {Function} callback - Callback function
     */
    offThemeChange(callback) {
        document.removeEventListener('themechange', callback);
    }
    
    /**
     * Destroy theme manager (cleanup)
     */
    destroy() {
        if (this.mediaQuery) {
            this.mediaQuery.removeEventListener('change', this.handleSystemChange);
        }
        
        if (this.themeToggle) {
            this.themeToggle.removeEventListener('click', this.cycleTheme);
            this.themeToggle.removeEventListener('keydown', this.handleToggleKeydown);
        }
        
        document.removeEventListener('keydown', this.handleKeyboardShortcuts);
        
        console.log('🎨 Theme Manager destroyed');
    }
}