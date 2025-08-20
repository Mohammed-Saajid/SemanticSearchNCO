import React from 'react'

function Results({ results }) {
  console.log(results);
  

  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <p>No results found. Try a different search query.</p>
      </div>
    );
  }

  return (
    <div className="results-container">
      <h2>Search Results ({results.length} found)</h2>
      {results.map((result, index) => (
        <div key={result.id || index} className="result-card">
          {/* Header with role information */}
          <div className="result-header">
            <h3 className="role-title">
              Role Number: {result.role_number || 'N/A'}
            </h3>
          </div>

          {/* Main content */}
          <div className="result-content">
            <h1>{result.title}</h1>
          </div>
        </div>
      ))}
    </div>
  )
}

export default Results