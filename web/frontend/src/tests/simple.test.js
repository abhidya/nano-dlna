import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Simple component for testing
const TestComponent = () => <button>Click me</button>;

describe('Simple Test', () => {
  test('renders a button', () => {
    render(<TestComponent />);
    const button = screen.getByText('Click me');
    expect(button).toBeInTheDocument();
    expect(button.tagName).toBe('BUTTON');
  });
});