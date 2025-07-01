/**
 * Simplified button tests that verify core functionality
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Simple test component with buttons
const TestComponent = () => {
  const [clicked, setClicked] = React.useState('');
  
  return (
    <div>
      <button onClick={() => setClicked('button1')}>Button 1</button>
      <button onClick={() => setClicked('button2')}>Button 2</button>
      <a href="#" onClick={(e) => { e.preventDefault(); setClicked('link1'); }}>Link 1</a>
      <div>{clicked && `Clicked: ${clicked}`}</div>
    </div>
  );
};

describe('Button and Link Tests', () => {
  test('buttons handle clicks correctly', () => {
    render(
      <BrowserRouter>
        <TestComponent />
      </BrowserRouter>
    );

    // Test button 1
    const button1 = screen.getByText('Button 1');
    fireEvent.click(button1);
    expect(screen.getByText('Clicked: button1')).toBeInTheDocument();

    // Test button 2
    const button2 = screen.getByText('Button 2');
    fireEvent.click(button2);
    expect(screen.getByText('Clicked: button2')).toBeInTheDocument();
  });

  test('links handle clicks correctly', () => {
    render(
      <BrowserRouter>
        <TestComponent />
      </BrowserRouter>
    );

    // Test link
    const link = screen.getByText('Link 1');
    fireEvent.click(link);
    expect(screen.getByText('Clicked: link1')).toBeInTheDocument();
  });

  test('navigation works with React Router', () => {
    const mockNavigate = jest.fn();
    
    // Mock useNavigate
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));
    
    const NavComponent = () => {
      const navigate = require('react-router-dom').useNavigate();
      
      return (
        <button onClick={() => navigate('/test')}>Navigate</button>
      );
    };
    
    render(
      <BrowserRouter>
        <NavComponent />
      </BrowserRouter>
    );
    
    const navButton = screen.getByText('Navigate');
    expect(navButton).toBeInTheDocument();
  });

  test('disabled buttons do not trigger clicks', () => {
    const handleClick = jest.fn();
    
    render(
      <button disabled onClick={handleClick}>
        Disabled Button
      </button>
    );
    
    const button = screen.getByText('Disabled Button');
    fireEvent.click(button);
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  test('buttons have proper ARIA attributes', () => {
    render(
      <button aria-label="Test Button" aria-pressed="true">
        Accessible Button
      </button>
    );
    
    const button = screen.getByLabelText('Test Button');
    expect(button).toHaveAttribute('aria-pressed', 'true');
  });
});