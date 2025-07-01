/**
 * Custom render function with providers
 */

import React from 'react';
import { render as rtlRender } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Create a default theme
const defaultTheme = createTheme();

// Custom render function that includes providers
export function render(
  ui,
  {
    initialRoute = '/',
    route = '/',
    theme = defaultTheme,
    ...renderOptions
  } = {}
) {
  function Wrapper({ children }) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <MemoryRouter initialEntries={[initialRoute]}>
          {children}
        </MemoryRouter>
      </ThemeProvider>
    );
  }

  // Set the route if needed
  if (route !== '/') {
    window.history.pushState({}, 'Test page', route);
  }

  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
}

// Re-export everything from testing library
export * from '@testing-library/react';

// Override the default render with our custom one
export { render as default };