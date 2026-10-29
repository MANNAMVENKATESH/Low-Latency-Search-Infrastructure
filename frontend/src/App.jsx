
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const RESEARCH = {
  baselineP95: 64.663,
  targetP95: 51.7304,
  run4: {
    fullSource: {
      average: 47.381,
      p50: 47.722,
      p95: 51.235,
      p99: 52.068,
      errors: 0,
      requests: 150,
    },
    selectedFields: {
      average: 47.265,
      p50: 47.729,
      p95: 50.799,
      p99: 54.141,
      errors: 0,
      requests: 150,
    },
  },
  relevance: {
    p5: { baseline: 92, improved: 100 },
    p10: { baseline: 88, improved: 96 },
    p20: { baseline: 88, improved: 88 },
  },
};

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [latency, setLatency] = useState(null);
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      const responses = await Promise.all([
        fetch(`${API}/health`),
        fetch(`${API}/metrics`),
        fetch(`${API}/availability`),
      ]);

      const data = await Promise.all(
        responses.map((response) => {
          if (!response.ok) throw new Error("API request failed");
          return response.json();
        })
      );

      setHealth(data[0]);
      setMetrics(data[1]);
      setAvailability(data[2]);
    } catch {
      setHealth(null);
      setError("Cannot connect to the API. Start FastAPI on port 8000.");
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  async function searchProducts(event) {
    event.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API}/search?q=${encodeURIComponent(query.trim())}&size=10`
      );

      const data = await response.json();

      setResults(data.results || []);
      setLatency(data.latency_ms ?? null);

      if (!response.ok || data.status !== "healthy") {
        setError(data.message || data.error || "Search service is degraded.");
      }
    } catch {
      setResults([]);
      setLatency(null);
      setError("Search failed. Check that FastAPI and Elasticsearch are running.");
    } finally {
      setLoading(false);
      loadDashboard();
    }
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">C30</div>
          <div>
            <h1>CLOUD-30</h1>
            <p>Low-Latency Search Infrastructure</p>
          </div>
        </div>
        <div className={`status ${health?.status === "healthy" ? "online" : "offline"}`}>
          <span />
          {health?.status === "healthy" ? "API Connected" : "API Disconnected"}
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">SEARCH INTELLIGENCE PLATFORM</p>
        <h2>Find what you need, faster.</h2>
        <p className="subtitle">
          Explore product search powered by Elasticsearch and FastAPI.
        </p>

        <form className="search-form" onSubmit={searchProducts}>
          <span className="search-icon">⌕</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try: laptop for students"
            aria-label="Search products"
          />
          <button disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="suggestions">
          Try:
          {[
            "laptop for students",
            "budget programming laptop",
            "mobile phone with good camera",
            "affordable gaming laptop",
            "wireless headphones",
          ].map((item) => (
            <button
              className="suggestion"
              key={item}
              onClick={() => setQuery(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="metrics-grid">
        <Metric
          label="Indexed Products"
          value={metrics?.documents?.toLocaleString() ?? "—"}
          detail="Documents in search index"
        />
        <Metric
          label="Search Latency"
          value={latency == null ? "—" : `${latency.toFixed(2)} ms`}
          detail="Most recent API search"
        />
        <Metric
          label="API Availability"
          value={
            availability
              ? `${availability.availability_percent.toFixed(2)}%`
              : "—"
          }
          detail="Current process statistics"
        />
        <Metric
          label="Elasticsearch"
          value={health?.elasticsearch ?? "Checking"}
          detail={
            health?.latency_ms != null
              ? `Health check: ${health.latency_ms} ms`
              : "Waiting for connection"
          }
        />
      </section>

      <section className="results-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">DISCOVERY</p>
            <h2>Search Results</h2>
          </div>
          <span className="result-count">{results.length} results</span>
        </div>

        {results.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⌕</div>
            <h3>Ready to search</h3>
            <p>Enter a product query above to see ranked results from Elasticsearch.</p>
          </div>
        ) : (
          <div className="products-grid">
            {results.map((product) => (
              <article className="product-card" key={product.id}>
                <div className="product-top">
                  <span className="rank">#{product.rank}</span>
                  <span className="category">
                    {product.category || "Product"}
                  </span>
                </div>
                <h3>{product.title || "Untitled product"}</h3>
                <p className="description">
                  {product.description || "No description available."}
                </p>
                <div className="product-meta">
                  <span>{product.brand || "Unknown brand"}</span>
                  <span>
                    {product.rating != null
                      ? `★ ${Number(product.rating).toFixed(1)}`
                      : "Not rated"}
                  </span>
                </div>
                <div className="product-bottom">
                  <strong>
                    {product.price != null
                      ? `₹${Number(product.price).toLocaleString("en-IN")}`
                      : "Price unavailable"}
                  </strong>
                  <span>Score: {Number(product.score || 0).toFixed(2)}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="research-panel">
        <div>
          <p className="eyebrow">PROJECT MONITOR</p>
          <h2>Infrastructure overview</h2>
          <p>Live values are fetched from your existing backend endpoints.</p>
        </div>
        <button className="refresh-button" onClick={loadDashboard}>
          Refresh metrics
        </button>
        <div className="infra-grid">
          <Info
            label="Cluster"
            value={health?.elasticsearch ?? "Unavailable"}
          />
          <Info
            label="Index"
            value={metrics?.index ?? "—"}
          />
          <Info
            label="Successful searches"
            value={availability?.successful_requests ?? "—"}
          />
          <Info
            label="Failed searches"
            value={availability?.failed_requests ?? "—"}
          />
        </div>
      </section>

      <section className="research-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">HISTORICAL EXPERIMENTS</p>
            <h2>Performance & Relevance</h2>
          </div>
          <span className="result-count">O2 baseline · O5 Run 4</span>
        </div>

        <div className="research-cards">
          <Metric
            label="O2 Baseline P95"
            value={`${RESEARCH.baselineP95} ms`}
            detail="Saved latency benchmark"
          />
          <Metric
            label="O5 Full-source P95"
            value={`${RESEARCH.run4.fullSource.p95} ms`}
            detail={`${RESEARCH.run4.fullSource.requests} requests · 0 errors`}
          />
          <Metric
            label="O5 Selected-fields P95"
            value={`${RESEARCH.run4.selectedFields.p95} ms`}
            detail={`${RESEARCH.run4.selectedFields.requests} requests · 0 errors`}
          />
          <Metric
            label="AC-2 P95 Target"
            value={`${RESEARCH.targetP95.toFixed(4)} ms`}
            detail="Must be at or below target"
          />
        </div>

        <div className="experiment-panel">
          <h3>O5 latency comparison</h3>
          <p className="panel-note">
            Lower P95 is better. Values are historical benchmark measurements,
            not live browser search latency.
          </p>

          {[
            { label: "O2 baseline", value: RESEARCH.baselineP95 },
            { label: "O5 full source", value: RESEARCH.run4.fullSource.p95 },
            { label: "O5 selected fields", value: RESEARCH.run4.selectedFields.p95 },
            { label: "AC-2 target", value: RESEARCH.targetP95 },
          ].map((item) => (
            <div className="bar-row" key={item.label}>
              <div className="bar-label">
                <span>{item.label}</span>
                <strong>{item.value.toFixed(3)} ms</strong>
              </div>
              <div className="bar-track">
                <div
                  className={`bar-fill ${item.label === "AC-2 target" ? "target-bar" : ""
                    }`}
                  style={{
                    width: `${Math.min(
                      (item.value / RESEARCH.baselineP95) * 100,
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>
          ))}

          <div className="acceptance-note">
            <strong>Run 4 result:</strong>{" "}
            Selected-fields P95 is{" "}
            {(
              RESEARCH.baselineP95 -
              RESEARCH.run4.selectedFields.p95
            ).toFixed(3)}{" "}
            ms below the O2 baseline and{" "}
            {(
              RESEARCH.targetP95 -
              RESEARCH.run4.selectedFields.p95
            ).toFixed(3)}{" "}
            ms below the AC-2 threshold. Full-source P95 is{" "}
            {(
              RESEARCH.run4.fullSource.p95 -
              RESEARCH.targetP95
            ).toFixed(3)}{" "}
            ms below the threshold.
          </div>
        </div>

        <div className="experiment-panel">
          <h3>Search relevance</h3>
          <p className="panel-note">
            Precision values from the saved O5 AC-1 relevance evidence.
          </p>

          {[
            { label: "Precision@5", ...RESEARCH.relevance.p5 },
            { label: "Precision@10", ...RESEARCH.relevance.p10 },
            { label: "Precision@20", ...RESEARCH.relevance.p20 },
          ].map((item) => (
            <div className="relevance-row" key={item.label}>
              <div className="bar-label">
                <span>{item.label}</span>
                <strong>
                  {item.baseline}% → {item.improved}%
                </strong>
              </div>
              <div className="comparison-bars">
                <div className="comparison-track">
                  <div
                    className="bar-fill baseline-bar"
                    style={{ width: `${item.baseline}%` }}
                  />
                </div>
                <div className="comparison-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${item.improved}%` }}
                  />
                </div>
              </div>
            </div>
          ))}

          <div className="acceptance-note">
            <strong>AC-1:</strong> Full acceptance remains unverified.
            The saved controlled data-change experiment recorded ranking
            changes but did not establish that the price change caused them.
          </div>
        </div>
      </section>

      <footer>
        <span>CLOUD-30 · Research Project</span>
        <span>React · FastAPI · Elasticsearch</span>
      </footer>
    </main>
  );
}

function Metric({ label, value, detail }) {
  return (
    <article className="metric-card">
      <p>{label}</p>
      <h3>{value}</h3>
      <span>{detail}</span>
    </article>
  );
}

function Info({ label, value }) {
  return (
    <div className="info-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;
