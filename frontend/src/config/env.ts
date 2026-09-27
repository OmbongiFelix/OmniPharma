/**
 * OmniPharma Frontend Environment and Runtime Configuration.
 *
 * Reads backend base URL from `import.meta.env.VITE_API_BASE_URL`
 * or defaults to `http://localhost:8000`.
 */

export const env = {
  /**
   * Base URL of the OmniPharma FastAPI backend.
   * Trailing slashes are stripped to avoid duplicate slashes in API calls.
   */
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, ''),
  /**
   * Whether the app is currently running in development mode.
   */
  isDev: Boolean(import.meta.env.DEV),
};
