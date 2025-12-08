/**
 * Zero-Trust AI Defense - Node.js Fallback System
 * Main entry point with integrated fallback orchestration
 */

import { createFallbackOrchestrator } from './lib/fallback-orchestrator.js';
import { DefenseServer } from './lib/server.js';
import { createMonitoringDashboard } from './lib/monitoring-dashboard.js';
import { PatternDetector } from './lib/detector.js';
import { RiskScorer } from './lib/risk-scorer.js';

async function main() {
  console.log('');
  console.log('╔══════════════════════════════════════════════════════╗');
  console.log('║  Zero-Trust AI Defense - Node.js Fallback System     ║');
  console.log('║                                                      ║');
  console.log('║  🛡️  Intelligent threat detection & isolation       ║');
  console.log('║  🔄 Automatic failover & recovery mechanisms        ║');
  console.log('║  📊 Real-time monitoring & diagnostics              ║');
  console.log('╚══════════════════════════════════════════════════════╝');
  console.log('');

  try {
    // ============================================
    // Step 1: Initialize Fallback Orchestrator
    // ============================================
    console.log('📋 Step 1: Initializing Fallback Orchestrator...');
    const orchestrator = createFallbackOrchestrator({
      enableAutoRecovery: true,
      enableCircuitBreaker: true,
      enableConnectionPool: true,
      healthConfig: {
        checkInterval: 10000,
        timeout: 5000
      },
      poolConfig: {
        minConnections: 2,
        maxConnections: 10
      }
    });

    // Initialize
    const initSuccess = await orchestrator.initialize();
    if (!initSuccess) {
      throw new Error('Orchestrator initialization failed');
    }

    // ============================================
    // Step 2: Setup Event Handlers
    // ============================================
    console.log('⚡ Step 2: Setting up event handlers...');
    
    orchestrator.on('fallbackModeActivated', (data) => {
      console.log('🔴 FALLBACK MODE ACTIVATED - Systems degraded');
    });

    orchestrator.on('fallbackModeDeactivated', (data) => {
      console.log('🟢 FALLBACK MODE DEACTIVATED - Systems recovered');
    });

    orchestrator.on('circuitBreakerOpen', (data) => {
      console.log(`⚠️  Circuit breaker opened for ${data.service}`);
    });

    orchestrator.on('fallbackActivated', (data) => {
      console.log(`🔄 Fallback activated for ${data.service}`);
    });

    // ============================================
    // Step 3: Register Health Checks
    // ============================================
    console.log('🔍 Step 3: Registering health checks...');

    // Detector health check
    orchestrator.registerHealthCheck('pattern-detector', async () => {
      const detector = new PatternDetector();
      const result = detector.analyzeRequest({
        timestamp: Date.now() / 1000,
        ip: '127.0.0.1',
        userAgent: 'test',
        endpoint: '/test'
      });
      if (!result.detectedPatterns) throw new Error('Detector failed');
    }, {
      interval: 30000,
      onFailure: () => console.warn('⚠️  Pattern detector failing')
    });

    // Scorer health check
    orchestrator.registerHealthCheck('risk-scorer', async () => {
      const scorer = new RiskScorer();
      const result = scorer.assessRisk({
        riskScore: 50,
        detectedPatterns: [],
        confidence: 0.8
      });
      if (!result.riskLevel) throw new Error('Scorer failed');
    }, {
      interval: 30000,
      onFailure: () => console.warn('⚠️  Risk scorer failing')
    });

    // ============================================
    // Step 4: Initialize Defense Server
    // ============================================
    console.log('🛡️  Step 4: Initializing Defense Server...');
    const defenseServer = new DefenseServer({ port: process.env.PORT || 3000 });
    
    // Integrate with orchestrator
    await defenseServer.initializeWithFallback(orchestrator);

    // ============================================
    // Step 5: Setup Monitoring Dashboard
    // ============================================
    console.log('📊 Step 5: Setting up Monitoring Dashboard...');
    const dashboard = createMonitoringDashboard(orchestrator, {
      port: 4000
    });

    // Listen for orchestrator events to update dashboard
    orchestrator.on('fallbackModeActivated', (data) => {
      dashboard.logEvent('fallback_mode_activated', data);
    });

    orchestrator.on('circuitBreakerOpen', (data) => {
      dashboard.logEvent('circuit_breaker_opened', data);
    });

    // ============================================
    // Step 6: Start Services
    // ============================================
    console.log('🚀 Step 6: Starting services...');
    defenseServer.start();
    dashboard.start();

    console.log('');
    console.log('✅ All systems initialized and running!');
    console.log('');
    console.log('📍 Service Endpoints:');
    console.log('   Defense Server:');
    console.log(`   • Main: http://localhost:${process.env.PORT || 3000}`);
    console.log(`   • Health: http://localhost:${process.env.PORT || 3000}/health`);
    console.log(`   • Metrics: http://localhost:${process.env.PORT || 3000}/metrics`);
    console.log(`   • Status: http://localhost:${process.env.PORT || 3000}/defense/status`);
    console.log(`   • Fallback Diagnostics: http://localhost:${process.env.PORT || 3000}/fallback/diagnostics`);
    console.log('');
    console.log('   Monitoring Dashboard:');
    console.log('   • Dashboard: http://localhost:4000/dashboard');
    console.log('   • Health: http://localhost:4000/health');
    console.log('   • Diagnostics: http://localhost:4000/diagnostics');
    console.log('');
    console.log('🔄 Fallback System Status:');
    const systemState = orchestrator.getSystemState();
    console.log(`   • Fallback Mode: ${systemState.fallbackActive ? '🔴 ACTIVE' : '🟢 OFF'}`);
    console.log(`   • System Health: ${systemState.health.overallStatus}`);
    console.log(`   • Components Down: ${systemState.health.summary.unhealthy + systemState.health.summary.critical}`);
    console.log('');
    console.log('💡 Tips:');
    console.log('   • Monitor the dashboard at http://localhost:4000/dashboard');
    console.log('   • Check /fallback/diagnostics for detailed system information');
    console.log('   • View circuit breaker status at /circuit-breakers endpoint');
    console.log('   • Review environment recommendations in diagnostics');
    console.log('');

    // ============================================
    // Step 7: Graceful Shutdown Handler
    // ============================================
    const shutdown = async (signal) => {
      console.log(`\n⏹️  Received ${signal}, shutting down gracefully...`);
      
      dashboard.stop();
      await orchestrator.shutdown();
      
      console.log('✅ Shutdown complete');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    console.error(error);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

export { main };
