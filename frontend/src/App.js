import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Home';
import Chat from './Chat';
import Navbar from './Navbar';
import { ThemeProvider } from './ThemeContext';
import './App.css';
import './responsive.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="App">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
