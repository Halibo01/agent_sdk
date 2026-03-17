---
title: Agent SDK - AI Agents & Swarms Framework
description: The lightweight, zero-dependency framework for building intelligent LLM agents and autonomous swarms.
keywords:
    - agent sdk
    - python ai framework
    - llm agents
    - multi-agent systems
    - swarm intelligence
    - python agents
    - agent
    - agent sdk core
    - agent core
    - local agent
hide:
  - navigation
  - toc
---

<!-- Custom Landing Page Styles -->
<style>
:root {
    --brand-primary: #6366f1;
    --brand-secondary: #a855f7;
    --brand-accent: #ec4899;
    --bg-dark: #0f172a;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --glass-bg: rgba(30, 41, 59, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
}

/* Override MkDocs Defaults for Landing Page */
.md-content { max-width: 100% !important; padding: 0 !important; }
.md-content__inner { padding: 0 !important; margin: 0 !important; }
.md-typeset h1, .md-typeset h2 { margin: 0; font-weight: 800; }

.landing-wrapper {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    color: var(--text-main);
    overflow-x: hidden;
}

/* HERO SECTION */
.hero-section {
    position: relative;
    padding: 8rem 2rem 6rem;
    text-align: center;
    background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0f172a 100%);
    overflow: hidden;
}

.hero-bg-glow {
    position: absolute;
    top: -50%;
    left: 50%;
    transform: translateX(-50%);
    width: 1000px;
    height: 1000px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    z-index: 0;
    pointer-events: none;
}

.hero-content {
    position: relative;
    z-index: 1;
    max-width: 800px;
    margin: 0 auto;
    opacity: 0;
    animation: fadeInUp 0.8s ease-out forwards;
}

.badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #818cf8;
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: 3.5rem;
    line-height: 1.2;
    margin-bottom: 1.5rem;
    letter-spacing: -0.02em;
}

.text-gradient {
    background: linear-gradient(135deg, #fff 30%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-muted);
    line-height: 1.6;
    margin-bottom: 2.5rem;
}

.cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

.btn {
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.2s ease;
    text-decoration: none !important;
}

.btn-primary {
    background: var(--brand-primary);
    color: white !important;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.23);
    background: #5558e6;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: white !important;
    border: 1px solid var(--glass-border);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
}

/* TERMINAL PREVIEW */
.terminal-wrapper {
    max-width: 800px;
    margin: 4rem auto 0;
    border-radius: 12px;
    border: 1px solid var(--glass-border);
    background: #0f172a; /* Fallback */
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    box-shadow: 0 20px 50px -12px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    opacity: 0;
    animation: fadeInUp 0.8s ease-out 0.3s forwards;
    text-align: left;
}

.terminal-header {
    background: rgba(255, 255, 255, 0.03);
    padding: 12px 16px;
    display: flex;
    gap: 8px;
    border-bottom: 1px solid var(--glass-border);
}

.dot { width: 12px; height: 12px; border-radius: 50%; }
.red { background: #ef4444; }
.yellow { background: #eab308; }
.green { background: #22c55e; }

.terminal-body {
    padding: 1.5rem;
    font-family: 'Fira Code', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    color: #e2e8f0;
}

.code-keyword { color: #c084fc; } /* purple */
.code-function { color: #60a5fa; } /* blue */
.code-string { color: #4ade80; } /* green */
.code-comment { color: #64748b; font-style: italic; }

/* FEATURES GRID */
.features-section {
    padding: 5rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.feature-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    padding: 2rem;
    border-radius: 1rem;
    transition: transform 0.3s ease, border-color 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
    border-color: var(--brand-primary);
}

.icon-box {
    width: 48px;
    height: 48px;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
    color: #818cf8;
    font-size: 1.5rem;
}

.feature-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: white;
}

.feature-desc {
    color: var(--text-muted);
    font-size: 0.95rem;
    line-height: 1.6;
}

/* ANIMATIONS */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* MOBILE */
@media (max-width: 768px) {
    .hero-title { font-size: 2.5rem; }
    .hero-section { padding: 4rem 1rem; }
    .features-grid { grid-template-columns: 1fr; }
}
</style>

<div class="landing-wrapper">

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="hero-bg-glow"></div>
        <div class="hero-content">
            <span class="badge">v0.2.0 Beta</span>
            <h1 class="hero-title">
                Build Intelligent <br>
                <span class="text-gradient">Agents & Swarms</span>
            </h1>
            <p class="hero-subtitle">
                A lightweight, zero-dependency Python framework. <br>
                Create model-agnostic AI agents, orchestrate swarms, and integrate memory in minutes.
            </p>
            
            <div class="cta-buttons">
                <a href="./docs/" class="btn btn-primary">Get Started</a>
                <a href="https://github.com/Halibo01/agent_sdk" class="btn btn-secondary">
                    <span class="twemoji">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 496 512"><path d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3.3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5.3-6.2 2.3zm44.2-1.7c-2.9.7-4.9 2.6-4.6 4.9.3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3.7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.6-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3.3 2.9 2.3 3.9 1.6 1 3.6.7 4.3-.7.7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3.7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3.7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z"/></svg>
                    </span>
                    GitHub
                </a>
            </div>

            <!-- Fake Terminal -->
            <div class="terminal-wrapper">
                <div class="terminal-header">
                    <div class="dot red"></div>
                    <div class="dot yellow"></div>
                    <div class="dot green"></div>
                </div>
                <div class="terminal-body">
                    <div><span class="code-keyword">from</span> agent_sdk <span class="code-keyword">import</span> Agent, Runner</div>
                    <br>
                    <div><span class="code-comment"># 1. Initialize your AI agent</span></div>
                    <div>agent = <span class="code-function">Agent</span>(</div>
                    <div>&nbsp;&nbsp;&nbsp;&nbsp;name=<span class="code-string">"DevBot"</span>,</div>
                    <div>&nbsp;&nbsp;&nbsp;&nbsp;model=<span class="code-string">"gpt-4o"</span>,</div>
                    <div>&nbsp;&nbsp;&nbsp;&nbsp;instructions=<span class="code-string">"You are a helpful coding assistant."</span></div>
                    <div>)</div>
                    <br>
                    <div><span class="code-comment"># 2. Run with streaming support</span></div>
                    <div>runner = <span class="code-function">Runner</span>()</div>
                    <div>runner.<span class="code-function">run_stream</span>(agent, <span class="code-string">"Analyze my dataset."</span>)</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
        <div class="features-grid">
            <a href="./docs/getting-started/quickstart/" class="feature-card" style="text-decoration: none; color: inherit; display: block;">
                <div class="icon-box">
                    <span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2m0 2a8 8 0 0 1 8 8 8 8 0 0 1-8 8 8 8 0 0 1-8-8 8 8 0 0 1 8-8m2.25 10.3c-.2.2-.5.2-.7 0L12 12.75l-1.55 1.55c-.2.2-.5.2-.7 0-.2-.2-.2-.5 0-.7l1.9-1.9c.2-.2.5-.2.7 0l1.9 1.9c.2.2.2.5 0 .7M8 12h8v2H8v-2Z"/></svg></span>
                </div>
                <h3 class="feature-title">Lightweight Core</h3>
                <p class="feature-desc">No heavy dependencies like LangChain. Built on pure Python for maximum speed and minimal bloat.</p>
            </a>

            <a href="./docs/modules/universal-llm-clients/" class="feature-card" style="text-decoration: none; color: inherit; display: block;">
                <div class="icon-box">
                    <span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2m0 2c-4.42 0-8 3.58-8 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8Z"/></svg></span>
                </div>
                <h3 class="feature-title">Model Agnostic</h3>
                <p class="feature-desc">Switch seamlessly between OpenAI, Gemini, Claude, Ollama, and other providers with a unified API.</p>
            </a>

            <a href="./docs/modules/middlewares/" class="feature-card" style="text-decoration: none; color: inherit; display: block;">
                <div class="icon-box">
                    <span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 16a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2m0-6a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2m0-6a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2Z"/></svg></span>
                </div>
                <h3 class="feature-title">Middleware System</h3>
                <p class="feature-desc">Extend capabilities with RAG, Human-in-the-Loop approval, Logging, and Safety checks easily.</p>
            </a>

            <a href="./docs/advanced/multi-agent-swarm-mesh/" class="feature-card" style="text-decoration: none; color: inherit; display: block;">
                <div class="icon-box">
                    <span class="twemoji"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M21 16.5c0 .38-.21.71-.53.88l-7.9 4.44c-.16.12-.36.18-.57.18-.21 0-.41-.06-.57-.18l-7.9-4.44A.991.991 0 0 1 3 16.5v-9c0-.38.21-.71.53-.88l7.9-4.44c.16-.12.36-.18.57-.18.21 0 .41.06.57.18l7.9 4.44c.32.17.53.5.53.88v9M12 4.15 6.04 7.5 12 10.85l5.96-3.35L12 4.15M5 15.91l6 3.38v-6.71L5 9.21v6.7m14 0v-6.7l-6 3.37v6.71l6-3.38Z"/></svg></span>
                </div>
                <h3 class="feature-title">Swarm Architecture</h3>
                <p class="feature-desc">Build autonomous mesh networks where agents collaborate, delegate, and handoff tasks intelligently.</p>
            </a>
        </div>
    </section>

</div>

<!-- JavaScript for Interactivity -->
<script>
    document.addEventListener("DOMContentLoaded", function() {
        // Simple intersection observer for fading in elements
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = "1";
                    entry.target.style.transform = "translateY(0)";
                }
            });
        });

        document.querySelectorAll('.feature-card').forEach(card => {
            card.style.opacity = "0";
            card.style.transform = "translateY(20px)";
            observer.observe(card);
        });
    });
</script>
