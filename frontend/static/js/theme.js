/**
 * LicenseLens Theme Manager
 * Handles Dark Mode and Light Mode switching, persistence, and event broadcasting.
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'licenselens-theme';
  const THEME_LIGHT = 'light';
  const THEME_DARK = 'dark';

  /**
   * Get the saved theme, or fallback to system preference.
   */
  function getPreferredTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === THEME_LIGHT || saved === THEME_DARK) {
      return saved;
    }
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? THEME_DARK
      : THEME_LIGHT;
  }

  /**
   * Apply theme attribute to root <html> element and notify listeners.
   */
  function applyTheme(theme, broadcast = true) {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;

    // Update all theme toggle buttons across the page
    updateToggleButtons(theme);

    if (broadcast) {
      window.dispatchEvent(
        new CustomEvent('themechange', {
          detail: { theme: theme }
        })
      );
    }
  }

  /**
   * Save theme and apply it.
   */
  function setTheme(theme) {
    localStorage.setItem(STORAGE_KEY, theme);
    applyTheme(theme, true);
  }

  /**
   * Toggle between light and dark themes.
   */
  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || THEME_LIGHT;
    const nextTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
    setTheme(nextTheme);
  }

  /**
   * Update visual state and accessibility attributes on toggle buttons.
   */
  function updateToggleButtons(theme) {
    const buttons = document.querySelectorAll('[data-theme-toggle]');
    buttons.forEach((btn) => {
      const isDark = theme === THEME_DARK;
      btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      btn.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      btn.classList.toggle('is-dark', isDark);

      const label = btn.querySelector('.theme-toggle-label');
      if (label) {
        label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
      }
    });
  }

  // Initialize theme on DOM ready
  function init() {
    const activeTheme = getPreferredTheme();
    applyTheme(activeTheme, false);

    // Attach click listeners to any [data-theme-toggle] elements
    document.addEventListener('click', function (event) {
      const toggleBtn = event.target.closest('[data-theme-toggle]');
      if (toggleBtn) {
        event.preventDefault();
        toggleTheme();
      }
    });

    // Listen for OS system theme changes if user hasn't explicitly saved a preference
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleSystemChange = (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
          applyTheme(e.matches ? THEME_DARK : THEME_LIGHT, true);
        }
      };

      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleSystemChange);
      } else if (mediaQuery.addListener) {
        mediaQuery.addListener(handleSystemChange);
      }
    }

    // Sync theme across multiple tabs
    window.addEventListener('storage', function (e) {
      if (e.key === STORAGE_KEY && e.newValue) {
        applyTheme(e.newValue, true);
      }
    });
  }

  // Expose helper globally
  window.LicenseLensTheme = {
    getTheme: function () {
      return document.documentElement.getAttribute('data-theme') || THEME_LIGHT;
    },
    setTheme: setTheme,
    toggleTheme: toggleTheme,
    applyTheme: applyTheme
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
