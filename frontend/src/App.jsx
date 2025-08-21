import './App.css';
import axios from 'axios';
import SearchBar from './components/SearchBar';
import Results from './components/Results';
import React, { useState, useEffect } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const baseURL = 'http://localhost:8000';

  // Load dark mode preference from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme) {
      setIsDarkMode(JSON.parse(savedTheme));
    }
  }, []);

  // Save dark mode preference and apply theme
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setHasSearched(true);
    try {
      const response = await axios.post(`${baseURL}/search`, {
        query: query,
      });
      console.log('Backend Response:', response.data);
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Error fetching search results:', error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`app ${isDarkMode ? 'dark-mode' : ''}`}>
      {/* Theme Toggle */}
      <button className="theme-toggle" onClick={toggleDarkMode}>
        {isDarkMode ? '☀️' : '🌙'}
      </button>

      {/* Main Title */}
      <div className="title-container">
        <h1 className="main-title">NCO Semantic Search</h1>
        <p className="subtitle">Find occupational roles using intelligent search</p>
      </div>

      {/* Search Section */}
      <div className="search-section">
        <SearchBar
          onSearch={handleSearch}
          query={query}
          setQuery={setQuery}
          isLoading={isLoading}
        />
      </div>

      {/* Results Section */}
      <div className="results-section">
        {isLoading && (
          <div className="loading">
            <p>Searching...</p>
          </div>
        )}
        {!isLoading && searchResults.length > 0 && (
          <Results results={searchResults} />
        )}
        {!isLoading && hasSearched && searchResults.length === 0 && (
          <div className="no-results">
            <p>No results found for "{query}"</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
