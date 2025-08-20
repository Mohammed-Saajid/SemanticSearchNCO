import './App.css';
import axios from 'axios';
import SearchBar from './components/searchBar';
import Results from './components/Results'; 
import React, { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);


  const baseURL = 'http://localhost:8000';

  const handleSearch = async (query) => {
    try {
      const response = await axios.post(`${baseURL}/search`, {
          query: query,
      });
      console.log(response.data);
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('Error fetching search results:', error);
    }
  };

  return (
    <div className="app">
        <SearchBar onSearch={handleSearch} query={query} setQuery={setQuery} />
        {searchResults.length > 0 && <Results results={searchResults} />}
    </div>
  );
}

export default App;
