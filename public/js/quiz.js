/**
 * quiz.js - interactive quiz renderer for TheBeakers
 *
 * renders quiz questions from story-data.json format
 * features: anti-hallucination warnings, claim references, curriculum grounding
 *
 * usage:
 *   const quiz = new BeakersQuiz('#quiz-container', quizData);
 *   quiz.render();
 */

class BeakersQuiz {
    constructor(containerSelector, quizData, options = {}) {
        this.container = document.querySelector(containerSelector);
        this.questions = quizData || [];
        this.currentIndex = 0;
        this.answers = new Array(this.questions.length).fill(null);
        this.options = {
            showProgress: true,
            showClaimRefs: true,
            showAntiHallucination: true,
            onComplete: null,
            ...options
        };
    }

    render() {
        if (!this.container || !this.questions.length) return;

        this.container.innerHTML = `
            <div class="bq-quiz">
                <div class="bq-header">Test Your Understanding</div>
                <div class="bq-body">
                    ${this.options.showProgress ? '<div class="bq-progress"></div>' : ''}
                    <div class="bq-question"></div>
                    <div class="bq-options"></div>
                    <div class="bq-feedback"></div>
                    <div class="bq-refs"></div>
                    <div class="bq-nav">
                        <button class="bq-btn bq-prev" disabled>Previous</button>
                        <button class="bq-btn bq-next">Next</button>
                    </div>
                </div>
            </div>
        `;

        this._injectStyles();
        this._bindEvents();
        this._renderQuestion(0);
        this._updateProgress();
    }

    _bindEvents() {
        const prevBtn = this.container.querySelector('.bq-prev');
        const nextBtn = this.container.querySelector('.bq-next');

        prevBtn.addEventListener('click', () => this._prevQuestion());
        nextBtn.addEventListener('click', () => this._nextQuestion());
    }

    _renderQuestion(idx) {
        if (idx < 0 || idx >= this.questions.length) return;
        this.currentIndex = idx;
        const q = this.questions[idx];

        // question text
        const questionEl = this.container.querySelector('.bq-question');
        questionEl.innerHTML = `
            <div class="bq-q-type">${this._formatType(q.type)} · ${q.difficulty || 'medium'}</div>
            <div class="bq-q-text">${q.prompt}</div>
        `;

        // options
        const optionsEl = this.container.querySelector('.bq-options');
        optionsEl.innerHTML = (q.options || []).map((opt, i) => `
            <div class="bq-option" data-index="${i}">${opt}</div>
        `).join('');

        // bind option clicks
        optionsEl.querySelectorAll('.bq-option').forEach(el => {
            el.addEventListener('click', () => this._selectOption(parseInt(el.dataset.index)));
        });

        // restore previous answer
        if (this.answers[idx] !== null) {
            this._showAnswer(q, this.answers[idx]);
        } else {
            this._hideFeedback();
        }

        // claim refs
        this._renderRefs(q);

        // nav buttons
        this.container.querySelector('.bq-prev').disabled = idx === 0;
        const nextBtn = this.container.querySelector('.bq-next');
        nextBtn.textContent = idx === this.questions.length - 1 ? 'Finish' : 'Next';

        this._updateProgress();
    }

    _selectOption(optIdx) {
        const q = this.questions[this.currentIndex];
        this.answers[this.currentIndex] = optIdx;
        this._showAnswer(q, optIdx);
        this._updateProgress();
    }

    _showAnswer(q, selectedIdx) {
        const options = this.container.querySelectorAll('.bq-option');
        const isCorrect = selectedIdx === q.correct_index;

        options.forEach((el, i) => {
            el.classList.remove('selected', 'correct', 'incorrect');
            if (i === selectedIdx) el.classList.add('selected');
            if (i === q.correct_index) el.classList.add('correct');
            else if (i === selectedIdx) el.classList.add('incorrect');
        });

        // feedback
        const feedbackEl = this.container.querySelector('.bq-feedback');
        feedbackEl.innerHTML = `
            <div class="bq-fb ${isCorrect ? 'correct' : 'incorrect'}">
                <div class="bq-fb-title">${isCorrect ? 'Correct!' : 'Not quite.'}</div>
                <div class="bq-fb-text">${q.justification || ''}</div>
                ${this.options.showAntiHallucination && q.anti_hallucination ? `
                    <div class="bq-fb-anti">Note: ${q.anti_hallucination}</div>
                ` : ''}
            </div>
        `;
    }

    _hideFeedback() {
        this.container.querySelector('.bq-feedback').innerHTML = '';
    }

    _renderRefs(q) {
        if (!this.options.showClaimRefs) return;
        const refsEl = this.container.querySelector('.bq-refs');
        const evidence = q.evidence || {};

        const parts = [];
        if (evidence.claim_ids?.length) {
            parts.push(`Claims: ${evidence.claim_ids.join(', ')}`);
        }
        if (evidence.curriculum_concept) {
            parts.push(`Curriculum: ${evidence.curriculum_concept}`);
        }

        refsEl.innerHTML = parts.length ? `<div class="bq-refs-text">${parts.join(' · ')}</div>` : '';
    }

    _updateProgress() {
        if (!this.options.showProgress) return;
        const progressEl = this.container.querySelector('.bq-progress');
        progressEl.innerHTML = this.questions.map((q, i) => {
            let cls = 'bq-dot';
            if (i === this.currentIndex) cls += ' current';
            else if (this.answers[i] !== null) {
                cls += this.answers[i] === q.correct_index ? ' correct' : ' incorrect';
            }
            return `<span class="${cls}"></span>`;
        }).join('');
    }

    _prevQuestion() {
        if (this.currentIndex > 0) {
            this._renderQuestion(this.currentIndex - 1);
        }
    }

    _nextQuestion() {
        if (this.currentIndex < this.questions.length - 1) {
            this._renderQuestion(this.currentIndex + 1);
        } else if (this.options.onComplete) {
            // calculate score
            const correct = this.answers.filter((a, i) => a === this.questions[i].correct_index).length;
            this.options.onComplete({ correct, total: this.questions.length, answers: this.answers });
        }
    }

    _formatType(type) {
        const types = {
            'claim_comprehension': 'Comprehension',
            'curriculum_application': 'Application',
            'limitation_awareness': 'Limitations',
            'data_reading': 'Data Reading',
            'calculation': 'Calculation'
        };
        return types[type] || type || 'Question';
    }

    _injectStyles() {
        if (document.getElementById('bq-styles')) return;
        const style = document.createElement('style');
        style.id = 'bq-styles';
        style.textContent = `
            .bq-quiz {
                background: #1e293b;
                border: 2px solid #14b8a6;
                border-radius: 16px;
                overflow: hidden;
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            .bq-header {
                background: #14b8a6;
                color: white;
                padding: 1rem 1.5rem;
                font-weight: 700;
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }
            .bq-body { padding: 1.5rem; }
            .bq-progress {
                display: flex;
                gap: 0.4rem;
                margin-bottom: 1.25rem;
            }
            .bq-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #334155;
            }
            .bq-dot.current { background: #14b8a6; }
            .bq-dot.correct { background: #10b981; }
            .bq-dot.incorrect { background: #ef4444; }
            .bq-q-type {
                font-size: 0.7rem;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }
            .bq-q-text {
                font-size: 1.1rem;
                color: #f1f5f9;
                line-height: 1.5;
                margin-bottom: 1.25rem;
            }
            .bq-options { display: flex; flex-direction: column; gap: 0.6rem; }
            .bq-option {
                padding: 0.9rem 1.1rem;
                background: #1a2744;
                border: 2px solid #334155;
                border-radius: 10px;
                cursor: pointer;
                color: #94a3b8;
                transition: all 0.2s;
                font-size: 0.95rem;
            }
            .bq-option:hover { border-color: #14b8a6; color: #f1f5f9; }
            .bq-option.selected { border-color: #3b82f6; background: rgba(59,130,246,0.1); }
            .bq-option.correct { border-color: #10b981; background: rgba(16,185,129,0.1); }
            .bq-option.incorrect { border-color: #ef4444; background: rgba(239,68,68,0.1); }
            .bq-fb {
                margin-top: 1.25rem;
                padding: 1rem;
                border-radius: 10px;
            }
            .bq-fb.correct { background: rgba(16,185,129,0.1); border-left: 3px solid #10b981; }
            .bq-fb.incorrect { background: rgba(239,68,68,0.1); border-left: 3px solid #ef4444; }
            .bq-fb-title { font-size: 0.9rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.4rem; }
            .bq-fb-text { font-size: 0.85rem; color: #94a3b8; }
            .bq-fb-anti {
                margin-top: 0.75rem;
                font-size: 0.8rem;
                color: #f59e0b;
                font-style: italic;
            }
            .bq-refs { margin-top: 1rem; }
            .bq-refs-text {
                font-size: 0.7rem;
                color: #64748b;
            }
            .bq-nav {
                margin-top: 1.5rem;
                display: flex;
                justify-content: space-between;
            }
            .bq-btn {
                padding: 0.6rem 1.2rem;
                background: #14b8a6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                font-size: 0.85rem;
            }
            .bq-btn:disabled { opacity: 0.4; cursor: not-allowed; }
            .bq-btn:hover:not(:disabled) { background: #0d9488; }
        `;
        document.head.appendChild(style);
    }

    // public methods
    getScore() {
        const correct = this.answers.filter((a, i) => a === this.questions[i].correct_index).length;
        return { correct, total: this.questions.length, percentage: Math.round(correct / this.questions.length * 100) };
    }

    reset() {
        this.answers = new Array(this.questions.length).fill(null);
        this._renderQuestion(0);
    }
}

// export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BeakersQuiz };
}
