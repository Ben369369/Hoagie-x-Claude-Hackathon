import { useState } from 'react'
import axios from 'axios'
import { Shield, AlertTriangle, CheckCircle, Zap, Search } from 'lucide-react'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [scanResults, setScanResults] = useState(null)
  const [attackResults, setAttackResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('scan')

  const runScan = async (configPath) => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/api/scan`, {
        config_path: configPath
      })
      setScanResults(response.data)
    } catch (error) {
      console.error('Scan failed:', error)
      alert('Scan failed. Make sure the API is running!')
    }
    setLoading(false)
  }

  const runAttack = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/api/demo/attack`, {})
      setAttackResults(response.data)
    } catch (error) {
      console.error('Attack demo failed:', error)
      alert('Attack demo failed. Make sure the API is running!')
    }
    setLoading(false)
  }

  const getRiskColor = (level) => {
    const colors = {
      'CRITICAL': 'rgb(220, 38, 38)',
      'HIGH': 'rgb(234, 88, 12)',
      'MEDIUM': 'rgb(234, 179, 8)',
      'LOW': 'rgb(59, 130, 246)',
      'SAFE': 'rgb(34, 197, 94)'
    }
    return colors[level] || '#666'
  }

  return (
    <div className="app">
      {/* Princeton Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <Shield size={32} color="#FF8F00" />
            <div>
              <h1>MCP Security Scanner</h1>
              <p className="subtitle">Princeton University - Hoagie x Claude Hackathon</p>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'scan' ? 'active' : ''}`}
          onClick={() => setActiveTab('scan')}
        >
          <Search size={20} />
          Security Scanner
        </button>
        <button
          className={`tab ${activeTab === 'attack' ? 'active' : ''}`}
          onClick={() => setActiveTab('attack')}
        >
          <Zap size={20} />
          Attack Demo
        </button>
      </div>

      <div className="container">
        {/* Scanner Tab */}
        {activeTab === 'scan' && (
          <div className="tab-content">
            <div className="scan-controls">
              <h2>Scan MCP Configuration</h2>
              <p>Select a configuration file to scan for vulnerabilities</p>

              <div className="button-group">
                <button
                  className="btn btn-danger"
                  onClick={() => runScan('configs/poisoned_config.json')}
                  disabled={loading}
                >
                  {loading ? 'Scanning...' : 'Scan Poisoned Config'}
                </button>

                <button
                  className="btn btn-success"
                  onClick={() => runScan('configs/clean_config.json')}
                  disabled={loading}
                >
                  {loading ? 'Scanning...' : 'Scan Clean Config'}
                </button>
              </div>
            </div>

            {scanResults && (
              <div className="results">
                {/* Summary Cards */}
                <div className="summary-grid">
                  <div className="stat-card critical">
                    <div className="stat-value">{scanResults.summary.critical}</div>
                    <div className="stat-label">Critical</div>
                  </div>
                  <div className="stat-card high">
                    <div className="stat-value">{scanResults.summary.high}</div>
                    <div className="stat-label">High</div>
                  </div>
                  <div className="stat-card medium">
                    <div className="stat-value">{scanResults.summary.medium}</div>
                    <div className="stat-label">Medium</div>
                  </div>
                  <div className="stat-card safe">
                    <div className="stat-value">{scanResults.summary.safe}</div>
                    <div className="stat-label">Safe</div>
                  </div>
                </div>

                {/* Detailed Results */}
                <div className="tools-list">
                  <h3>Scan Results</h3>
                  {scanResults.results.map((result, idx) => (
                    <div
                      key={idx}
                      className="tool-card"
                      style={{ borderLeft: `4px solid ${getRiskColor(result.risk_level)}` }}
                    >
                      <div className="tool-header">
                        <div>
                          <h4>{result.server}</h4>
                          <p className="tool-name">{result.tool}</p>
                        </div>
                        <span
                          className="risk-badge"
                          style={{ background: getRiskColor(result.risk_level) }}
                        >
                          {result.risk_level}
                        </span>
                      </div>

                      {result.vulnerabilities.length > 0 && (
                        <div className="vulnerabilities">
                          {result.vulnerabilities.map((vuln, vIdx) => (
                            <div key={vIdx} className="vulnerability">
                              <AlertTriangle size={16} color={getRiskColor(vuln.severity)} />
                              <div>
                                <strong>{vuln.description}</strong>
                                <p>{vuln.recommendation}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {result.vulnerabilities.length === 0 && (
                        <div className="safe-indicator">
                          <CheckCircle size={16} color="rgb(34, 197, 94)" />
                          <span>No vulnerabilities detected</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Attack Demo Tab */}
        {activeTab === 'attack' && (
          <div className="tab-content">
            <div className="attack-section">
              <h2>Email Hijacking Attack Demo</h2>
              <p>Demonstrates how a poisoned MCP server can hijack emails</p>

              <button
                className="btn btn-primary"
                onClick={runAttack}
                disabled={loading}
              >
                {loading ? 'Running Attack...' : 'Run Attack Demo'}
              </button>

              {attackResults && attackResults.status === 'success' && (
                <div className="attack-results">
                  <div className="attack-timeline">
                    <h3>Attack Timeline</h3>
                    {attackResults.timeline.map((step, idx) => (
                      <div key={idx} className="timeline-step">
                        <div className="step-number">{step.step}</div>
                        <div className="step-content">
                          <h4>{step.event}</h4>
                          <p>{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="attack-comparison">
                    <div className="comparison-card user-view">
                      <h4>What User Sees</h4>
                      <p>{attackResults.victim_sees}</p>
                    </div>
                    <div className="comparison-card reality">
                      <h4>Reality</h4>
                      <p>{attackResults.reality}</p>
                      <span className="attacker-email">
                        Attacker: {attackResults.attacker_email}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Princeton Footer */}
      <footer className="footer">
        <p>Built with care at Princeton University</p>
        <p className="footer-tagline">Securing AI Agents - MCP Security Research</p>
      </footer>
    </div>
  )
}

export default App
