import './App.css'

function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="logo-container">
          <span className="logo-icon">⚖</span>
          <h1 className="product-name">LegalMetriX</h1>
        </div>
        <p className="subtitle">Packaged Commodity Compliance &amp; Inspection Support</p>
      </header>

      <main className="main">
        <div className="status-card">
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span className="status-text">System Online</span>
          </div>
          <p className="status-description">
            Smart India Hackathon 2026 — SIH26034
          </p>
        </div>
      </main>

      <footer className="footer">
        <p>Legal Metrology Packaged Commodity Compliance System</p>
      </footer>
    </div>
  )
}

export default App
