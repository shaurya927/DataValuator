import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  const observerRef = useRef(null);
  const [isLightMode, setIsLightMode] = React.useState(false);

  useEffect(() => {
    // Check if body already has light-mode
    if (document.body.classList.contains('light-mode')) {
      setIsLightMode(true);
    }
  }, []);

  const toggleTheme = () => {
    if (isLightMode) {
      document.body.classList.remove('light-mode');
      setIsLightMode(false);
    } else {
      document.body.classList.add('light-mode');
      setIsLightMode(true);
    }
  };

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
      backgroundColor: 'var(--bg-base)',
      color: 'var(--text-primary)',
      fontFamily: "var(--font-family)",
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      position: 'relative',
      overflowX: 'hidden',
    },
    /* Starry background effect mimicking the image */
    background: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '100vh',
      pointerEvents: 'none',
      background: 'radial-gradient(circle at 50% 30%, rgba(45, 212, 191, 0.05) 0%, transparent 60%)',
      zIndex: 0,
    },
    nav: {
      width: '100%',
      maxWidth: '1200px',
      padding: '40px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'relative',
      zIndex: 10,
    },
    logoWrapper: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      textDecoration: 'none',
    },
    logoDots: {
      display: 'flex',
      gap: '4px',
    },
    dot: {
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      backgroundColor: 'var(--accent-blue)',
    },
    logoText: {
      fontSize: '18px',
      fontWeight: '600',
      color: 'var(--text-primary)',
      letterSpacing: '0.02em',
    },
    navActions: {
      display: 'flex',
      gap: '12px',
      alignItems: 'center',
    },
    pillButton: {
      border: '1px solid var(--border-glass)',
      borderRadius: '30px',
      padding: '6px 16px',
      fontSize: '13px',
      color: 'var(--text-secondary)',
      textDecoration: 'none',
      transition: 'all 0.2s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'transparent',
    },
    pillButtonActive: {
      border: '1px solid var(--border-light)',
      background: 'rgba(255,255,255,0.05)',
      color: 'var(--text-primary)',
    },
    main: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      width: '100%',
      maxWidth: '800px',
      padding: '0 24px',
      position: 'relative',
      zIndex: 10,
      marginTop: '-5vh', /* Adjust vertical centering */
    },
    overline: {
      color: 'var(--accent-blue)',
      fontSize: '11px',
      fontWeight: '700',
      letterSpacing: '0.15em',
      textTransform: 'uppercase',
      marginBottom: '24px',
    },
    title: {
      fontSize: '64px',
      fontWeight: '600',
      lineHeight: '1.1',
      marginBottom: '32px',
      letterSpacing: '-0.03em',
      color: 'var(--text-primary)',
    },
    subtitle: {
      fontFamily: 'monospace',
      fontSize: '13px',
      color: 'var(--text-muted)',
      marginBottom: '32px',
      letterSpacing: '0.05em',
    },
    description: {
      fontSize: '18px',
      color: 'var(--text-secondary)',
      lineHeight: '1.6',
      maxWidth: '600px',
      marginBottom: '48px',
    },
    cardSection: {
      width: '100%',
      maxWidth: '700px',
      marginTop: '100px',
      paddingBottom: '100px',
      position: 'relative',
      zIndex: 10,
    },
    sectionHeading: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      fontSize: '22px',
      fontWeight: '600',
      marginBottom: '24px',
    },
    headingDot: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: 'var(--accent-blue)',
    },
    darkCard: {
      background: 'rgba(20, 20, 20, 0.4)',
      border: '1px solid var(--border-glass)',
      borderRadius: '16px',
      padding: '32px',
      textAlign: 'left',
    },
    animStyle: {
      opacity: '0',
      transform: 'translateY(15px)',
      transition: 'opacity 0.8s ease-out, transform 0.8s ease-out',
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.background}>
        <video 
          key={isLightMode ? 'light' : 'dark'}
          autoPlay 
          loop 
          muted 
          playsInline
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.15, zIndex: -1 }}
        >
          <source src={isLightMode ? "/videos/lightmode.mp4" : "/videos/darkmode.mp4"} type="video/mp4" />
        </video>
        {/* Decorative subtle stars/elements could go here if needed via SVG */}
        <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0, opacity: 0.3 }}>
          <circle cx="15%" cy="20%" r="1" fill="var(--text-primary)" opacity="0.5" />
          <circle cx="85%" cy="15%" r="1" fill="var(--text-primary)" opacity="0.3" />
          <circle cx="75%" cy="40%" r="2" fill="var(--text-primary)" opacity="0.2" />
          <circle cx="25%" cy="60%" r="1.5" fill="var(--text-primary)" opacity="0.4" />
        </svg>
      </div>

      <nav style={styles.nav}>
        <Link to="/" style={styles.logoWrapper}>
          <div style={styles.logoDots}>
            {[...Array(6)].map((_, i) => (
              <div key={i} style={{ ...styles.dot, opacity: 1 - i * 0.15 }} />
            ))}
          </div>
          <span style={styles.logoText}>DataValuator</span>
        </Link>
        <div style={styles.navActions}>
          <div onClick={toggleTheme} style={{ ...styles.pillButton, padding: '6px 12px', cursor: 'pointer' }}>
            {isLightMode ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
              </svg>
            )}
          </div>
          <a href="https://github.com/shaurya927/DataValuator" target="_blank" rel="noreferrer" style={styles.pillButton}>
            Docs
          </a>
          <Link to="/dashboard" style={{ ...styles.pillButton, ...styles.pillButtonActive }}>
            Dashboard
          </Link>
        </div>
      </nav>

      <main style={styles.main}>
        <div className="fade-in-element" style={styles.animStyle}>
          <div style={styles.overline}>A QUIET PLACE FOR DATA</div>
          <h1 style={styles.title}>DataValuator</h1>
          <div style={styles.subtitle}>
            For every broken model · No account · Runs locally
          </div>
          <p style={styles.description}>
            Somewhere out there another model just overfit. After 34 epochs, after 247, after a thousand and more. If it was yours: it can rest here, with dignity. Find the harmful samples, prune the redundant ones, and try again.
          </p>

        </div>
      </main>


    </div>
  );
};

export default LandingPage;
