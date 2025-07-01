/**
 * Environment abstraction layer
 * Provides safe access to browser APIs in both browser and test environments
 */

const isBrowser = typeof window !== 'undefined';
const isTest = process.env.NODE_ENV === 'test';

export const getWindow = () => {
  if (isBrowser && !isTest) {
    return window;
  }
  // Mock window for test environment
  return {
    location: {
      protocol: 'http:',
      host: 'localhost:3000',
      hostname: 'localhost',
      port: '3000',
      pathname: '/',
      href: 'http://localhost:3000/',
      origin: 'http://localhost:3000',
      reload: jest?.fn() || (() => {})
    },
    open: jest?.fn() || (() => ({ closed: false })),
    navigator: {
      userAgent: 'Mozilla/5.0 (Testing) Jest/29.0'
    },
    localStorage: {
      getItem: jest?.fn() || (() => null),
      setItem: jest?.fn() || (() => {}),
      removeItem: jest?.fn() || (() => {}),
      clear: jest?.fn() || (() => {})
    }
  };
};

export const getDocument = () => {
  if (isBrowser) {
    return document;
  }
  // Mock document for test environment
  return {
    getElementById: jest?.fn() || (() => null),
    querySelector: jest?.fn() || (() => null),
    querySelectorAll: jest?.fn() || (() => []),
    createElement: jest?.fn() || (() => ({})),
    activeElement: null
  };
};

export const getLocation = () => {
  const window = getWindow();
  return window.location;
};

export const getBaseURL = () => {
  const location = getLocation();
  return `${location.protocol}//${location.host}`;
};

export const getApiBaseURL = () => {
  return `${getBaseURL()}/api`;
};

export const isTestEnvironment = () => isTest;
export const isBrowserEnvironment = () => isBrowser;