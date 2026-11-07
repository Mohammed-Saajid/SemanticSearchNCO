import './App.css';
import apiClient from './api.js';
import SearchBar from './components/SearchBar';
import Results from './components/Results';
import React, { useState, useEffect } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [topK, setTopK] = useState(10);
  const [hasSearched, setHasSearched] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [bm25Weight, setBm25Weight] = useState(0.4);
  const [vectorWeight, setVectorWeight] = useState(0.6);

  useEffect(() => {
    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme) {
      setIsDarkMode(JSON.parse(savedTheme));
    }
  }, []);

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

  const fetchResults = async (searchQuery, currentOffset) => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    try {
      const response = await apiClient.post('/search', {
        query: searchQuery,
        top_k: topK,
        offset: currentOffset,
        bm25_weight: bm25Weight,
        vector_weight: vectorWeight,
      });
      setSearchResults(response.data.results || []);
      setTotalCount(response.data.total ?? 0);
      setErrorMessage('');
    } catch (error) {
      console.error('Error fetching search results:', error);
      setSearchResults([]);
      setTotalCount(0);
      setErrorMessage(error.response?.data?.detail || 'Unable to complete the search. Please check the connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (newQuery) => {
    setQuery(newQuery);
    setOffset(0);
    setHasSearched(true);
    await fetchResults(newQuery, 0);
  };

  const handlePrev = async () => {
    const newOffset = Math.max(0, offset - topK);
    setOffset(newOffset);
    await fetchResults(query, newOffset);
  };

  const handleNext = async () => {
    const newOffset = offset + topK;
    setOffset(newOffset);
    await fetchResults(query, newOffset);
  };

  return (
    <div className={`app ${isDarkMode ? 'dark-mode' : ''}`}>
      <button className="theme-toggle" onClick={toggleDarkMode}>
        {isDarkMode ? '\u2600\uFE0F' : '\uD83C\uDF19'}
      </button>

      <div className="title-container">
        <h1 className="main-title">NCO Semantic Search</h1>
        <p className="subtitle">Find occupational roles using intelligent search</p>
      </div>

      <div className="search-section">
        <SearchBar
          onSearch={handleSearch}
          query={query}
          setQuery={setQuery}
          isLoading={isLoading}
          topK={topK}
          setTopK={setTopK}
          bm25Weight={bm25Weight}
          setBm25Weight={setBm25Weight}
          vectorWeight={vectorWeight}
          setVectorWeight={setVectorWeight}
        />
      </div>

      {hasSearched && (
        <p className="result-info">
          Showing {searchResults.length} of {totalCount} results
        </p>
      )}
      {totalCount > topK && (
        <div className="pagination-controls">
          <button onClick={handlePrev} disabled={offset === 0}>Prev</button>
          <span>Page {Math.floor(offset / topK) + 1}</span>
          <button onClick={handleNext} disabled={offset + topK >= totalCount}>Next</button>
        </div>
      )}
      <div className="results-section">
        {isLoading && (
          <div className="loading">
            <p>Searching...</p>
          </div>
        )}
        {!isLoading && errorMessage && (
          <div className="no-results error-message" role="alert"><p>{errorMessage}</p></div>
        )}
        {!isLoading && !errorMessage && searchResults.length > 0 && (
          <Results results={searchResults} totalCount={totalCount} />
        )}
        {!isLoading && !errorMessage && hasSearched && searchResults.length === 0 && (
          <div className="no-results">
            <p>No results found for "{query}"</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
