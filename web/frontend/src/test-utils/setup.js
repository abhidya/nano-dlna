/**
 * Global test setup and configuration
 */

// Import testing library matchers
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Suppress console errors during tests (optional)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    // Filter out known React warnings that are not relevant to tests
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('ReactDOMTestUtils.act') ||
       args[0].includes('React Router Future Flag Warning'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Clean up after each test
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();
  
  // Clear local storage
  if (window.localStorage) {
    window.localStorage.clear();
  }
});