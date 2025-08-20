import React from 'react'

function SearchBar({ onSearch ,query ,setQuery }) {

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={() => onSearch(query)}>Search</button>
    </div>
  );
}

export default SearchBar;