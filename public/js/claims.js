/**
 * claims.js - claim ledger renderer for TheBeakers
 *
 * renders evidence-backed claims from story-data.json
 * features: expandable ledger, evidence typing, inline references
 *
 * usage:
 *   const ledger = new ClaimLedger('#claims-container', claimsData);
 *   ledger.render();
 */

class ClaimLedger {
    constructor(containerSelector, claims, options = {}) {
        this.container = document.querySelector(containerSelector);
        this.claims = claims || [];
        this.options = {
            expandedByDefault: false,
            showEvidence: true,
            showCitations: true,
            onClaimClick: null,
            ...options
        };
        this.isExpanded = this.options.expandedByDefault;
    }

    render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="cl-ledger ${this.isExpanded ? 'open' : ''}">
                <div class="cl-header">
                    <h3 class="cl-title">Evidence Ledger</h3>
                    <span class="cl-count">${this.claims.length} claims</span>
                    <span class="cl-toggle">${this.isExpanded ? '−' : '+'}</span>
                </div>
                <div class="cl-body">
                    ${this._renderClaims()}
                </div>
            </div>
        `;

        this._injectStyles();
        this._bindEvents();
    }

    _renderClaims() {
        return this.claims.map(c => `
            <div class="cl-item" data-id="${c.id}">
                <span class="cl-id">${c.id.replace('C','')}</span>
                <div class="cl-content">
                    <div class="cl-text">${c.claim}</div>
                    ${this.options.showEvidence ? `
                        <div class="cl-meta">
                            <span class="cl-evidence ${c.evidence_type || 'inferred'}">${c.evidence_type || 'inferred'}</span>
                            ${this.options.showCitations && c.citation_key ? `<span class="cl-cite">${c.citation_key}</span>` : ''}
                            ${c.panel_ids?.length ? `<span class="cl-panels">Panels: ${c.panel_ids.join(', ')}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    _bindEvents() {
        // toggle expand/collapse
        const header = this.container.querySelector('.cl-header');
        header.addEventListener('click', () => this.toggle());

        // claim clicks
        if (this.options.onClaimClick) {
            this.container.querySelectorAll('.cl-item').forEach(el => {
                el.addEventListener('click', () => {
                    this.options.onClaimClick(el.dataset.id);
                });
            });
        }
    }

    toggle() {
        this.isExpanded = !this.isExpanded;
        const ledger = this.container.querySelector('.cl-ledger');
        ledger.classList.toggle('open', this.isExpanded);
        this.container.querySelector('.cl-toggle').textContent = this.isExpanded ? '−' : '+';
    }

    expand() {
        if (!this.isExpanded) this.toggle();
    }

    collapse() {
        if (this.isExpanded) this.toggle();
    }

    highlightClaim(claimId) {
        this.expand();
        const el = this.container.querySelector(`[data-id="${claimId}"]`);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.classList.add('highlight');
            setTimeout(() => el.classList.remove('highlight'), 1500);
        }
    }

    getClaim(claimId) {
        return this.claims.find(c => c.id === claimId);
    }

    _injectStyles() {
        if (document.getElementById('cl-styles')) return;
        const style = document.createElement('style');
        style.id = 'cl-styles';
        style.textContent = `
            .cl-ledger {
                background: linear-gradient(135deg, rgba(139,92,246,0.1), rgba(59,130,246,0.05));
                border: 1px solid #8b5cf6;
                border-radius: 12px;
                overflow: hidden;
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            .cl-header {
                padding: 0.9rem 1.25rem;
                border-bottom: 1px solid rgba(139,92,246,0.3);
                display: flex;
                align-items: center;
                cursor: pointer;
                user-select: none;
            }
            .cl-header:hover { background: rgba(139,92,246,0.1); }
            .cl-title {
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b5cf6;
                margin: 0;
            }
            .cl-count {
                margin-left: auto;
                font-size: 0.7rem;
                color: #64748b;
            }
            .cl-toggle {
                margin-left: 0.75rem;
                font-size: 1.1rem;
                color: #8b5cf6;
            }
            .cl-body {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease;
            }
            .cl-ledger.open .cl-body {
                max-height: 800px;
                overflow-y: auto;
            }
            .cl-item {
                padding: 0.75rem 1.25rem;
                border-bottom: 1px solid rgba(139,92,246,0.15);
                display: flex;
                gap: 0.75rem;
                transition: background 0.2s;
            }
            .cl-item:last-child { border-bottom: none; }
            .cl-item:hover { background: rgba(139,92,246,0.1); cursor: pointer; }
            .cl-item.highlight { background: rgba(139,92,246,0.25); }
            .cl-id {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 26px;
                height: 26px;
                background: #8b5cf6;
                color: white;
                font-size: 0.65rem;
                font-weight: 700;
                border-radius: 50%;
                flex-shrink: 0;
            }
            .cl-content { flex: 1; min-width: 0; }
            .cl-text {
                font-size: 0.85rem;
                color: #f1f5f9;
                margin-bottom: 0.25rem;
                line-height: 1.4;
            }
            .cl-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                font-size: 0.65rem;
            }
            .cl-evidence {
                padding: 0.15rem 0.4rem;
                border-radius: 4px;
                font-weight: 600;
                text-transform: uppercase;
            }
            .cl-evidence.empirical { background: rgba(16,185,129,0.2); color: #10b981; }
            .cl-evidence.computed { background: rgba(59,130,246,0.2); color: #3b82f6; }
            .cl-evidence.cited { background: rgba(245,158,11,0.2); color: #f59e0b; }
            .cl-evidence.inferred { background: rgba(100,116,139,0.2); color: #64748b; }
            .cl-cite, .cl-panels { color: #64748b; }
        `;
        document.head.appendChild(style);
    }
}

// static method to create inline claim references
ClaimLedger.createRef = function(claimId, onClick) {
    const span = document.createElement('span');
    span.className = 'cl-ref';
    span.textContent = claimId.replace('C', '');
    span.style.cssText = `
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 16px;
        height: 16px;
        background: #8b5cf6;
        color: white;
        font-size: 0.55rem;
        font-weight: 700;
        border-radius: 50%;
        cursor: pointer;
        vertical-align: super;
        margin: 0 2px;
    `;
    if (onClick) span.addEventListener('click', () => onClick(claimId));
    return span;
};

// export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ClaimLedger };
}
