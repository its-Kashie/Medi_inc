import React from 'react';
import '../App.css';

function HomePage() {
    return (
        <div className="page-container fade-in">
            {/* Page Header */}
            <div className="page-header">
                <h1 className="page-title">Welcome to HealthLink360</h1>
                <p className="page-subtitle">
                    Enterprise Healthcare Management & Intelligence System
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                <div className="stat-card">
                    <div className="stat-value">1,247</div>
                    <div className="stat-label">Active Patients</div>
                    <div className="stat-change positive">↑ 12% from last month</div>
                </div>

                <div className="stat-card">
                    <div className="stat-value">89</div>
                    <div className="stat-label">Emergency Cases</div>
                    <div className="stat-change negative">↓ 5% from last month</div>
                </div>

                <div className="stat-card">
                    <div className="stat-value">342</div>
                    <div className="stat-label">Appointments Today</div>
                    <div className="stat-change positive">↑ 8% from yesterday</div>
                </div>

                <div className="stat-card">
                    <div className="stat-value">98.5%</div>
                    <div className="stat-label">System Uptime</div>
                    <div className="stat-change positive">Excellent</div>
                </div>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-3">
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🏥 Healthcare Operations</h3>
                    </div>
                    <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                        Real-time patient care, emergency response, and clinical services across all departments.
                    </p>
                    <ul style={{ color: 'var(--gray-700)', lineHeight: '1.8' }}>
                        <li>✓ Emergency & Ambulance Tracking</li>
                        <li>✓ Maternal Health Management</li>
                        <li>✓ Mental Health Services</li>
                        <li>✓ Pharmacy & Prescription Management</li>
                        <li>✓ Medical Waste Tracking</li>
                    </ul>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">📊 Analytics & Reporting</h3>
                    </div>
                    <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                        Comprehensive reporting system with AI-powered insights and WHO/NIH compliance.
                    </p>
                    <ul style={{ color: 'var(--gray-700)', lineHeight: '1.8' }}>
                        <li>✓ Department-Level Analytics</li>
                        <li>✓ Hospital Performance Metrics</li>
                        <li>✓ National Health Statistics</li>
                        <li>✓ WHO-Compliant Reports</li>
                        <li>✓ Research Data Aggregation</li>
                    </ul>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🤖 AI Agent System</h3>
                    </div>
                    <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                        14+ specialized AI agents for automated workflows and intelligent decision support.
                    </p>
                    <ul style={{ color: 'var(--gray-700)', lineHeight: '1.8' }}>
                        <li>✓ Department-Specific Agents</li>
                        <li>✓ Hospital Central Orchestrator</li>
                        <li>✓ NIH Coordination Agent</li>
                        <li>✓ R&D Research Agent</li>
                        <li>✓ Automated Report Generation</li>
                    </ul>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🔐 Security & Compliance</h3>
                    </div>
                    <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                        Enterprise-grade security with multi-level PII protection and audit logging.
                    </p>
                    <ul style={{ color: 'var(--gray-700)', lineHeight: '1.8' }}>
                        <li>✓ Multi-Level PII Redaction</li>
                        <li>✓ CNIC Verification & Encryption</li>
                        <li>✓ Medico-Legal Isolation</li>
                        <li>✓ 7-Year Audit Trail</li>
                        <li>✓ HIPAA & GDPR Compliance</li>
                    </ul>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">🌐 National Scale</h3>
                    </div>
                    <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                        Designed to support nationwide healthcare coordination and policy-making.
                    </p>
                    <ul style={{ color: 'var(--gray-700)', lineHeight: '1.8' }}>
                        <li>✓ Multi-Hospital Network</li>
                        <li>✓ Quarterly Reporting Workflow</li>
                        <li>✓ NIH Integration</li>
                        <li>✓ University Research Collaboration</li>
                        <li>✓ WHO Reporting Pipeline</li>
                    </ul>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">⚡ Real-Time Operations</h3>
                    </div>
                    <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                        WebSocket-powered real-time updates for critical healthcare operations.
                    </p>
                    <ul style={{ color: 'var(--gray-700)', lineHeight: '1.8' }}>
                        <li>✓ Live Emergency Tracking</li>
                        <li>✓ Bed Availability Updates</li>
                        <li>✓ Patient Status Monitoring</li>
                        <li>✓ Critical Alert System</li>
                        <li>✓ Real-Time Dashboards</li>
                    </ul>
                </div>
            </div>

            {/* Quick Actions */}
            <div style={{ marginTop: '3rem', textAlign: 'center' }}>
                <h2 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '1.5rem', color: 'var(--gray-900)' }}>
                    Quick Actions
                </h2>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button className="btn btn-primary">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '20px', height: '20px' }}>
                            <path d="M12 5v14M5 12h14" />
                        </svg>
                        New Patient
                    </button>
                    <button className="btn btn-success">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '20px', height: '20px' }}>
                            <circle cx="12" cy="12" r="10" />
                            <path d="M12 8v4M12 16h.01" />
                        </svg>
                        Emergency Alert
                    </button>
                    <button className="btn btn-primary">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '20px', height: '20px' }}>
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                        </svg>
                        Generate Report
                    </button>
                </div>
            </div>

            {/* System Status */}
            <div className="card" style={{ marginTop: '3rem' }}>
                <div className="card-header">
                    <h3 className="card-title">System Status</h3>
                    <span style={{
                        padding: '0.5rem 1rem',
                        background: 'var(--accent-100)',
                        color: 'var(--accent-700)',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '0.875rem',
                        fontWeight: '600'
                    }}>
                        ● All Systems Operational
                    </span>
                </div>
                <div className="grid grid-4">
                    <div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Backend Core</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--success)' }}>✓ Online</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Backend Reporting</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--success)' }}>✓ Online</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Database</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--success)' }}>✓ Connected</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>MCP Servers</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--success)' }}>✓ Active (5/5)</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default HomePage;
