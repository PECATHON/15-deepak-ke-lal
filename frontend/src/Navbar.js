import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { IoHome, IoChatbubbles, IoSparkles, IoMoon, IoSunny } from 'react-icons/io5';
import { useTheme } from './ThemeContext';

const Navbar = () => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.nav 
      className="navbar"
      role="navigation"
      aria-label="Main navigation"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="nav-container">
        <div className="nav-brand" role="banner">
          <IoSparkles className="brand-icon" aria-hidden="true" />
          <span>Ava Travel</span>
        </div>
        
        <div className={`nav-links ${isMenuOpen ? 'active' : ''}`} role="menubar">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => setIsMenuOpen(false)}
            role="menuitem"
            aria-label="Home page"
          >
            <IoHome size={18} aria-hidden="true" />
            <span>Home</span>
          </Link>
          <Link 
            to="/chat" 
            className={`nav-link ${location.pathname === '/chat' ? 'active' : ''}`}
            onClick={() => setIsMenuOpen(false)}
            role="menuitem"
            aria-label="Chat with travel assistant"
          >
            <IoChatbubbles size={18} aria-hidden="true" />
            <span>Chat</span>
          </Link>
        </div>
        
        <div className="nav-controls">
          <motion.button
            className="theme-toggle"
            onClick={toggleTheme}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <IoSunny size={20} /> : <IoMoon size={20} />}
          </motion.button>
          
          <button 
            className={`hamburger ${isMenuOpen ? 'active' : ''}`}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label={isMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={isMenuOpen}
            aria-controls="nav-links"
          >
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
          </button>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;