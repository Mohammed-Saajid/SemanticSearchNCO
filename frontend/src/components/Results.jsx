import React, { useState } from 'react'

function Results({ results, totalCount }) {
  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <p>No results found. Try a different search query.</p>
      </div>
    );
  }

  return (
    <div className="results-container">
      <h2>Search Results ({totalCount ?? results.length} found)</h2>
      {results.map((result, index) => (
        <ResultCard key={result.id || index} result={result} />
      ))}
    </div>
  );
}

function ResultCard({ result }) {
  const [expanded, setExpanded] = useState(false);
  const description = removeLeadingTitle(result.chunk_text, result.role_title);

  return (
    <div className="result-card">
      <div className="result-header">
        <h3 className="role-title">
          {result.role_title || 'Role Title Not Available'}
        </h3>
        <span className="role-number">
          #{result.rank} · Role {result.role_number || 'N/A'}
        </span>
      </div>

      <div className="result-content">
        <div className="section-label">Job description</div>
        <div className="chunk-text">
          <p>{description || 'No description available'}</p>
        </div>
      </div>

      <div className="role-details">
        <DetailItem label="Occupational Title" value={result['Occupational Title']} />
        <DetailItem label="NCO 2015" value={result['NCO 2015']} />
        <DetailItem label="NCO 2004" value={result['NCO 2004']} />
        <DetailItem label="Division" value={result['Division']} />
        <DetailItem label="Sub Division" value={result['Sub Division']} />
        <DetailItem label="Group" value={result['Group']} />
        <DetailItem label="Family" value={result['Family']} />
      </div>

      <div className="result-scores">
        <div className="score-item">
          <span className="score-label">Combined</span>
          <span className="score-value">{formatScore(result.combined_score)}</span>
        </div>
        {result.bm25_score != null && (
          <div className="score-item">
            <span className="score-label">BM25</span>
            <span className="score-value">{formatScore(result.bm25_score)}</span>
          </div>
        )}
        {result.vector_score != null && (
          <div className="score-item">
            <span className="score-label">Vector</span>
            <span className="score-value">{formatScore(result.vector_score)}</span>
          </div>
        )}
      </div>

      <button
        className="details-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? 'Hide raw data' : 'Show raw data'}
      </button>

      {expanded && (
        <div className="debug-info">
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function removeLeadingTitle(description, title) {
  if (!description) return '';
  if (!title) return description;

  const normalizedDescription = description.trimStart();
  const normalizedTitle = title.trim();
  const titlePattern = new RegExp(`^${normalizedTitle.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')}\\s*`, 'i');

  return normalizedDescription.replace(titlePattern, '').trim();
}

function DetailItem({ label, value }) {
  if (!value) return null;
  return (
    <div className="detail-item">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  );
}

function formatScore(score) {
  if (score == null) return 'N/A';
  return Number(score).toFixed(4);
}

export default Results;
