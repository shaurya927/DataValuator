import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { DashboardIcon, DatabaseIcon, ZapIcon, SearchIcon, FlaskIcon, ChevronLeftIcon, ChevronRightIcon } from './Icons';

const navItems = [
  { path: '/dashboard', icon: <DashboardIcon size={18} />, label: 'Dashboard' },
  { path: '/datasets', icon: <DatabaseIcon size={18} />, label: 'Datasets' },
  { path: '/training', icon: <ZapIcon size={18} />, label: 'Training' },
  { path: '/explorer', icon: <SearchIcon size={18} />, label: 'Explorer' },
  { path: '/experiments', icon: <FlaskIcon size={18} />, label: 'Experiments' },
];

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const pageTitle =
    navItems.find((item) => location.pathname.startsWith(item.path))?.label ||
    'DataValuator';

  return (
    <div style={styles.root}>
      {/* ───── Sidebar ───── */}
      <aside
        style={{
          ...styles.sidebar,
          width: collapsed ? 64 : 240,
        }}
      >
        {/* Logo bar */}
        <div style={styles.sidebarHeader}>
          {!collapsed && <span style={styles.logo}>DataValuator</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={styles.collapseBtn}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRightIcon size={14} /> : <ChevronLeftIcon size={14} />}
          </button>
        </div>

        {/* Navigation */}
        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
              title={collapsed ? item.label : undefined}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              {!collapsed && <span style={styles.navLabel}>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        {!collapsed && (
          <div style={styles.sidebarFooter}>
            <p>DataValuator v1.0</p>
            <p style={{ marginTop: 4, opacity: 0.5 }}>Training Data Intelligence</p>
          </div>
        )}
      </aside>

      {/* ───── Main area ───── */}
      <main style={styles.main}>
        {/* Top bar */}
        <header style={styles.topBar}>
          <h1 style={styles.pageTitle}>{pageTitle}</h1>
        </header>

        {/* Content */}
        <div style={styles.content}>
          <div className="animate-fade-in" style={styles.contentInner}>
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}

/* ─── Inline styles using CSS custom properties ─── */
const styles = {
  root: {
    display: 'flex',
    height: '100vh',
    overflow: 'hidden',
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    background: 'linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%)',
    borderRight: '1px solid var(--border-glass)',
    transition: 'width var(--transition-slow)',
    overflow: 'hidden',
    flexShrink: 0,
  },
  sidebarHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 'var(--space-4)',
    borderBottom: '1px solid var(--border-glass)',
    height: 64,
    minHeight: 64,
  },
  logo: {
    fontWeight: 700,
    fontSize: 'var(--font-lg)',
    color: 'var(--text-primary)',
    letterSpacing: '0.02em',
    whiteSpace: 'nowrap',
  },
  collapseBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-muted)',
    cursor: 'pointer',
    fontSize: 'var(--font-sm)',
    padding: 4,
    borderRadius: 'var(--radius-sm)',
    transition: 'color var(--transition-fast)',
  },
  nav: {
    flex: 1,
    padding: 'var(--space-4) var(--space-2)',
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--space-1)',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--space-3)',
    padding: 'var(--space-2) var(--space-3)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    transition: 'all var(--transition-fast)',
    borderLeftWidth: '2px',
    borderLeftStyle: 'solid',
    borderLeftColor: 'transparent',
    whiteSpace: 'nowrap',
  },
  navLinkActive: {
    background: 'var(--accent-blue-alpha)',
    color: 'var(--accent-blue)',
    borderLeftColor: 'var(--accent-blue)',
  },
  navIcon: {
    fontSize: 'var(--font-xl)',
    width: 24,
    textAlign: 'center',
    flexShrink: 0,
  },
  navLabel: {
    fontWeight: 500,
    fontSize: 'var(--font-sm)',
  },
  sidebarFooter: {
    padding: 'var(--space-4)',
    borderTop: '1px solid var(--border-glass)',
    fontSize: 'var(--font-xs)',
    color: 'var(--text-muted)',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
    overflow: 'hidden',
    backgroundColor: 'var(--bg-base)',
  },
  topBar: {
    height: 64,
    minHeight: 64,
    borderBottom: '1px solid var(--border-glass)',
    display: 'flex',
    alignItems: 'center',
    padding: '0 var(--space-6)',
    background: 'rgba(30, 41, 59, 0.5)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
  },
  pageTitle: {
    fontSize: 'var(--font-xl)',
    fontWeight: 600,
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    padding: 'var(--space-6)',
  },
  contentInner: {
    maxWidth: 1280,
    margin: '0 auto',
  },
};
