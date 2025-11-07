/**
 * Zero-Trust AI Defense - Node.js Fallback Library
 * 
 * Provides alternative implementations when Python components are unavailable
 * or for integration with JavaScript-based systems.
 */

export { PatternDetector } from './lib/detector.js';
export { HoneypotGenerator } from './lib/honeypot-generator.js';
export { MetricsCollector } from './lib/metrics.js';
export { DockerController } from './lib/docker-controller.js';
export { createDefenseServer } from './lib/server.js';
export { RiskScorer } from './lib/risk-scorer.js';

/**
 * Quick start function for fallback mode
 */
export async function initializeFallbackDefense(config = {}) {
  const { PatternDetector } = await import('./lib/detector.js');
  const { RiskScorer } = await import('./lib/risk-scorer.js');
  const { MetricsCollector } = await import('./lib/metrics.js');
  
  const detector = new PatternDetector(config.rules || {});
  const riskScorer = new RiskScorer(config.thresholds || {});
  const metrics = new MetricsCollector();
  
  console.log('[FALLBACK] Zero-Trust AI Defense initialized in Node.js mode');
  
  return {
    detector,
    riskScorer,
    metrics,
    processRequest: async (requestData) => {
      // Detect patterns
      const detection = detector.analyzeRequest(requestData);
      
      // Score risk
      const risk = riskScorer.assessRisk(detection);
      
      // Record metrics
      metrics.recordRequest(requestData, risk);
      
      return {
        action: risk.riskScore > 80 ? 'countermeasures' : 'allow',
        riskScore: risk.riskScore,
        riskLevel: risk.riskLevel,
        threatCategory: risk.threatCategory,
        detection
      };
    }
  };
}

// CLI mode
if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/')}`) {
  console.log('Zero-Trust AI Defense - Node.js Fallback Library');
  console.log('=================================================');
  console.log('');
  console.log('Usage:');
  console.log('  npm start              # Run fallback defense');
  console.log('  npm run server         # Start HTTP server');
  console.log('  npm run honeypot       # Start honeypot server');
  console.log('  npm run detector       # Test pattern detector');
  console.log('');
  
  const defense = await initializeFallbackDefense();
  
  // Test with sample data
  const testRequest = {
    timestamp: Date.now() / 1000,
    ip: '203.0.113.42',
    userAgent: 'Mozilla/5.0 (bot)',
    endpoint: '/api/users',
    params: { id: "1' OR '1'='1" },
    headers: {},
    content: "SELECT * FROM users WHERE id='1' OR '1'='1'",
    sessionId: 'test_session'
  };
  
  console.log('Testing with SQL injection sample...');
  const result = await defense.processRequest(testRequest);
  console.log('Result:', JSON.stringify(result, null, 2));
}
