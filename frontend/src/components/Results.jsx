import React from 'react'

function Results({ results }) {
  console.log('Results received:', results);

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
              {result.role_title || result.title || 'Role Title Not Available'}
            </h3>
            <span className="role-number">Role {result.role_number || 'N/A'}</span>
          </div>

          {/* Main content */}
          <div className="result-content">
            <div className="chunk-text">
              <p>{result.chunk_text || result.description || 'No description available'}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default Results