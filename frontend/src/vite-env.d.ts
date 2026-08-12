/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the FastAPI backend, including the /api/v1 prefix. */
  readonly VITE_API_BASE_URL?: string;
  /** "true" enables the mock adapter and the Demo Mode banner. */
  readonly VITE_USE_MOCK_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
