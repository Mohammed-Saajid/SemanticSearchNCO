import React from 'react'

function SearchBar({ onSearch, query, setQuery, isLoading, topK, setTopK }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      onSearch(query);
    }
  };

  return (
    <div className="search-bar-container">
      <div className="search-bar">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search for roles (e.g., 'software engineer', 'doctor', 'teacher')..."
          className="search-input"
          disabled={isLoading}
        />
        <button
          onClick={() => onSearch(query)}
          className="search-button"
          disabled={isLoading || !query.trim()}
          title={isLoading ? 'Searching...' : 'Search'}
        >
          {isLoading ? (
            <svg className="search-icon spinning" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="31.416" strokeDashoffset="31.416">
                <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite" />
                <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite" />
              </circle>
            </svg>
          ) : (
            <svg className="search-icon" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
              <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" />
            </svg>
          )}
        </button>
      </div>
      <div className="search-options">
        <label className="weight-label">
          <span>Results per page</span>
          <input type="number" min="1" max="100" step="1" value={topK}
            onChange={(e) => setTopK(Math.min(100, Math.max(1, Number(e.target.value) || 1)))}
            className="results-count-input" disabled={isLoading} />
        </label>
      </div>
    </div>
  );
}

export default SearchBar;
