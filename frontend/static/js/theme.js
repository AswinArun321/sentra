/**
 * SENTRA Theme Manager
 * Configured strictly for Light Mode across the platform.
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'sentra-theme';
  const LEGACY_STORAGE_KEY = 'licenselens-theme';
  const THEME_LIGHT = 'light';

  /**
   * Always returns light theme.
   */
  function getPreferredTheme() {
    return THEME_LIGHT;
  }

  /**
   * Apply light theme attribute to root <html> element.
   */
  function applyTheme(theme = THEME_LIGHT, broadcast = true) {
    document.documentElement.setAttribute('data-theme', THEME_LIGHT);
    document.documentElement.style.colorScheme = THEME_LIGHT;

    try {
      localStorage.setItem(STORAGE_KEY, THEME_LIGHT);
      localStorage.setItem(LEGACY_STORAGE_KEY, THEME_LIGHT);
    } catch (e) {}

    if (broadcast) {
      window.dispatchEvent(
        new CustomEvent('themechange', {
          detail: { theme: THEME_LIGHT }
        })
      );
    }
  }

  /**
   * Theme setter locked to light mode.
   */
  function setTheme(_theme) {
    applyTheme(THEME_LIGHT, true);
  }

  /**
   * Toggle is a no-op / maintains light mode.
   */
  function toggleTheme() {
    applyTheme(THEME_LIGHT, true);
  }

  // Initialize theme on DOM ready
  function init() {
    applyTheme(THEME_LIGHT, false);
  }

  // Expose helper globally for backward compatibility
  window.SentraTheme = {
    getTheme: function () {
      return THEME_LIGHT;
    },
    setTheme: setTheme,
    toggleTheme: toggleTheme,
    applyTheme: applyTheme
  };
  // Backward compatibility alias
  window.LicenseLensTheme = window.SentraTheme;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
