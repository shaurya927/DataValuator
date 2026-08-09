import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ActivityIcon, ScissorsIcon, SearchIcon } from '../components/Icons';

const LandingPage = () => {
  const observerRef = useRef(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }
        });
      },
      { threshold: 0.1 }
    );

    const elements = document.querySelectorAll('.fade-in-element');
    elements.forEach((el) => {
      observerRef.current.observe(el);
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  const styles = {
    container: {
      backgroundColor: 'var(--bg-base, #0B1120)',
      color: 'var(--text-primary, #F8FAFC)',
      fontFamily: "'Inter', sans-serif",
      minHeight: '100vh',
      overflowX: 'hidden',
    },
    nav: {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: '70px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 5%',
      backgroundColor: 'var(--bg-glass, rgba(30, 41, 59, 0.6))',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-glass, rgba(148, 163, 184, 0.1))',
      zIndex: 1000,
    },
    logo: {
      fontSize: '24px',
      fontWeight: '700',
      color: 'var(--text-primary, #F8FAFC)',
      textDecoration: 'none',
    },
    navLinks: {
      display: 'flex',
      gap: '32px',
      alignItems: 'center',
    },
    navLink: {
      color: 'var(--text-secondary, #94A3B8)',
      textDecoration: 'none',
      fontSize: '15px',
      fontWeight: '500',
      transition: 'color 0.2s ease',
    },
    navButton: {
      backgroundColor: 'var(--accent-blue, #3B82F6)',
      color: '#fff',
      padding: '8px 20px',
      borderRadius: 'var(--radius-md, 8px)',
      textDecoration: 'none',
      fontSize: '15px',
      fontWeight: '600',
      transition: 'background-color 0.2s ease',
    },
    hero: {
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      textAlign: 'center',
      padding: '0 20px',
      background: 'radial-gradient(circle at 50% 0%, var(--accent-blue-alpha, rgba(59, 130, 246, 0.2)) 0%, transparent 60%)',
      paddingTop: '70px',
    },
    heroTitle: {
      fontSize: '64px',
      fontWeight: '800',
      lineHeight: '1.2',
      marginBottom: '24px',
      maxWidth: '800px',
      background: 'linear-gradient(to right, #F8FAFC, #94A3B8)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    heroSubtitle: {
      fontSize: '20px',
      color: 'var(--text-secondary, #94A3B8)',
      maxWidth: '650px',
      marginBottom: '48px',
      lineHeight: '1.6',
    },
    heroButtons: {
      display: 'flex',
      gap: '16px',
    },
    primaryButton: {
      backgroundColor: 'var(--accent-blue, #3B82F6)',
      color: '#fff',
      padding: '14px 28px',
      borderRadius: 'var(--radius-lg, 12px)',
      textDecoration: 'none',
      fontSize: '16px',
      fontWeight: '600',
      transition: 'all 0.2s ease',
      boxShadow: 'var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.4))',
      border: 'none',
    },
    secondaryButton: {
      backgroundColor: 'transparent',
      color: 'var(--text-primary, #F8FAFC)',
      padding: '14px 28px',
      borderRadius: 'var(--radius-lg, 12px)',
      textDecoration: 'none',
      fontSize: '16px',
      fontWeight: '600',
      border: '1px solid var(--border-glass, rgba(148, 163, 184, 0.1))',
      transition: 'all 0.2s ease',
    },
    section: {
      padding: '100px 5%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    },
    sectionTitle: {
      fontSize: '36px',
      fontWeight: '700',
      marginBottom: '64px',
      textAlign: 'center',
    },
    featuresGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
      gap: '32px',
      width: '100%',
      maxWidth: '1200px',
    },
    card: {
      backgroundColor: 'var(--bg-glass, rgba(30, 41, 59, 0.6))',
      border: '1px solid var(--border-glass, rgba(148, 163, 184, 0.1))',
      borderRadius: 'var(--radius-xl, 16px)',
      padding: '40px 32px',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-start',
      transition: 'transform 0.3s ease, background-color 0.3s ease',
    },
    iconWrapper: {
      width: '48px',
      height: '48px',
      borderRadius: 'var(--radius-md, 8px)',
      backgroundColor: 'var(--accent-blue-alpha, rgba(59, 130, 246, 0.2))',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: '24px',
      color: 'var(--accent-blue, #3B82F6)',
    },
    cardTitle: {
      fontSize: '24px',
      fontWeight: '600',
      marginBottom: '16px',
    },
    cardText: {
      color: 'var(--text-secondary, #94A3B8)',
      lineHeight: '1.6',
      fontSize: '16px',
    },
    stepsContainer: {
      display: 'flex',
      flexDirection: 'column',
      gap: '48px',
      width: '100%',
      maxWidth: '800px',
    },
    stepItem: {
      display: 'flex',
      gap: '24px',
      alignItems: 'flex-start',
    },
    stepNumber: {
      width: '48px',
      height: '48px',
      borderRadius: '50%',
      backgroundColor: 'var(--accent-blue, #3B82F6)',
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '20px',
      fontWeight: '700',
      flexShrink: 0,
    },
    stepContent: {
      display: 'flex',
      flexDirection: 'column',
      paddingTop: '8px',
    },
    stepTitle: {
      fontSize: '24px',
      fontWeight: '600',
      marginBottom: '12px',
    },
    stepText: {
      color: 'var(--text-secondary, #94A3B8)',
      lineHeight: '1.6',
      fontSize: '16px',
    },
    statsRow: {
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'center',
      gap: '48px',
      padding: '64px 5%',
      backgroundColor: 'var(--bg-surface-elevated, #1E293B)',
      width: '100%',
    },
    statItem: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center',
    },
    statValue: {
      fontSize: '48px',
      fontWeight: '800',
      color: 'var(--text-primary, #F8FAFC)',
      marginBottom: '8px',
    },
    statLabel: {
      fontSize: '16px',
      color: 'var(--text-secondary, #94A3B8)',
      fontWeight: '500',
    },
    footer: {
      borderTop: '1px solid var(--border-glass, rgba(148, 163, 184, 0.1))',
      padding: '48px 5%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '24px',
      backgroundColor: 'var(--bg-base, #0B1120)',
    },
    footerBrand: {
      fontSize: '20px',
      fontWeight: '700',
      color: 'var(--text-primary, #F8FAFC)',
    },
    footerText: {
      color: 'var(--text-muted, #64748B)',
      fontSize: '14px',
    },
    footerLinks: {
      display: 'flex',
      gap: '24px',
    },
    footerLink: {
      color: 'var(--text-secondary, #94A3B8)',
      textDecoration: 'none',
      fontSize: '14px',
      transition: 'color 0.2s ease',
    },
    animStyle: {
      opacity: '0',
      transform: 'translateY(20px)',
      transition: 'opacity 0.6s ease-out, transform 0.6s ease-out',
    }
  };

  return (
    <div style={styles.container}>
      {/* Navigation */}
      <nav style={styles.nav}>
        <a href="#" style={styles.logo}>DataValuator</a>
        <div style={styles.navLinks}>
          <a href="#features" style={styles.navLink}>Features</a>
          <a href="#how-it-works" style={styles.navLink}>How It Works</a>
          <a href="#docs" style={styles.navLink}>Documentation</a>
          <Link to="/dashboard" style={styles.navButton}>Get Started</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={styles.hero}>
        <div className="fade-in-element" style={{...styles.animStyle, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <h1 style={styles.heroTitle}>Understand Which Training Data Actually Matters</h1>
          <p style={styles.heroSubtitle}>
            DataValuator helps ML practitioners discover high-value, redundant, and harmful training samples through advanced data valuation methods.
          </p>
          <div style={styles.heroButtons}>
            <Link to="/dashboard" style={styles.primaryButton}>Get Started</Link>
            <a href="#features" style={styles.secondaryButton}>Learn More</a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" style={styles.section}>
        <h2 className="fade-in-element" style={{...styles.sectionTitle, ...styles.animStyle}}>Features</h2>
        <div style={styles.featuresGrid}>
          <div className="fade-in-element" style={{...styles.card, ...styles.animStyle, transitionDelay: '0.1s'}}>
            <div style={styles.iconWrapper}>
              <ActivityIcon />
            </div>
            <h3 style={styles.cardTitle}>Data Valuation</h3>
            <p style={styles.cardText}>
              Quantify each training sample's contribution using Leave-One-Out, Data Shapley, and more.
            </p>
          </div>
          <div className="fade-in-element" style={{...styles.card, ...styles.animStyle, transitionDelay: '0.2s'}}>
            <div style={styles.iconWrapper}>
              <ScissorsIcon />
            </div>
            <h3 style={styles.cardTitle}>Smart Pruning</h3>
            <p style={styles.cardText}>
              Remove harmful and redundant data to improve model accuracy and reduce training time.
            </p>
          </div>
          <div className="fade-in-element" style={{...styles.card, ...styles.animStyle, transitionDelay: '0.3s'}}>
            <div style={styles.iconWrapper}>
              <SearchIcon />
            </div>
            <h3 style={styles.cardTitle}>Visual Explorer</h3>
            <p style={styles.cardText}>
              Interactive scatter plots and tables to explore sample values and identify outliers.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" style={styles.section}>
        <h2 className="fade-in-element" style={{...styles.sectionTitle, ...styles.animStyle}}>How It Works</h2>
        <div style={styles.stepsContainer}>
          <div className="fade-in-element" style={{...styles.stepItem, ...styles.animStyle, transitionDelay: '0.1s'}}>
            <div style={styles.stepNumber}>1</div>
            <div style={styles.stepContent}>
              <h3 style={styles.stepTitle}>Upload Dataset</h3>
              <p style={styles.stepText}>
                Import your training data in CSV or image format. We auto-detect features and labels.
              </p>
            </div>
          </div>
          <div className="fade-in-element" style={{...styles.stepItem, ...styles.animStyle, transitionDelay: '0.2s'}}>
            <div style={styles.stepNumber}>2</div>
            <div style={styles.stepContent}>
              <h3 style={styles.stepTitle}>Train &amp; Valuate</h3>
              <p style={styles.stepText}>
                Choose a model and valuation method. Track progress in real-time as each sample gets scored.
              </p>
            </div>
          </div>
          <div className="fade-in-element" style={{...styles.stepItem, ...styles.animStyle, transitionDelay: '0.3s'}}>
            <div style={styles.stepNumber}>3</div>
            <div style={styles.stepContent}>
              <h3 style={styles.stepTitle}>Explore &amp; Optimize</h3>
              <p style={styles.stepText}>
                Visualize data values, prune harmful samples, and retrain with a cleaner dataset.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section style={styles.statsRow}>
        <div className="fade-in-element" style={{...styles.statItem, ...styles.animStyle, transitionDelay: '0.1s'}}>
          <div style={styles.statValue}>5+</div>
          <div style={styles.statLabel}>Valuation Methods</div>
        </div>
        <div className="fade-in-element" style={{...styles.statItem, ...styles.animStyle, transitionDelay: '0.2s'}}>
          <div style={styles.statValue}>Real-time</div>
          <div style={styles.statLabel}>Training Insights</div>
        </div>
        <div className="fade-in-element" style={{...styles.statItem, ...styles.animStyle, transitionDelay: '0.3s'}}>
          <div style={styles.statValue}>100%</div>
          <div style={styles.statLabel}>Open Source</div>
        </div>
        <div className="fade-in-element" style={{...styles.statItem, ...styles.animStyle, transitionDelay: '0.4s'}}>
          <div style={styles.statValue}>Built for</div>
          <div style={styles.statLabel}>ML Engineers</div>
        </div>
      </section>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.footerBrand}>DataValuator</div>
        <div style={styles.footerText}>Training Data Intelligence.</div>
        <div style={styles.footerLinks}>
          <a href="#" style={styles.footerLink}>GitHub</a>
          <a href="#" style={styles.footerLink}>Privacy</a>
          <a href="#" style={styles.footerLink}>Terms</a>
        </div>
        <div style={styles.footerText}>© 2024 DataValuator.</div>
      </footer>
    </div>
  );
};

export default LandingPage;
