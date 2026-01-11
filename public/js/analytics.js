/**
 * analytics.js - TheBeakers analytics wrapper
 *
 * tracks: view, scroll depth, audio play, quiz submit, subscribe
 * uses: Plausible (privacy-friendly, simple)
 *
 * setup:
 * 1. create account at plausible.io or self-host
 * 2. add domain: thebeakers.com
 * 3. enable script below
 */

(function() {
    // config - update PLAUSIBLE_DOMAIN when ready
    const PLAUSIBLE_DOMAIN = 'thebeakers.com';
    const PLAUSIBLE_API = 'https://plausible.io/api/event';  // or self-hosted URL
    const ENABLED = false;  // set true when plausible is configured

    if (!ENABLED) return;

    // send event to plausible
    function track(name, props = {}) {
        if (!ENABLED) return;

        const payload = {
            n: name,
            u: window.location.href,
            d: PLAUSIBLE_DOMAIN,
            r: document.referrer || null,
            p: JSON.stringify(props)
        };

        navigator.sendBeacon(PLAUSIBLE_API, JSON.stringify(payload));
    }

    // track pageview
    track('pageview');

    // track scroll depth buckets (25%, 50%, 75%, 100%)
    const scrollBuckets = [25, 50, 75, 100];
    const scrollTracked = new Set();

    function checkScroll() {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight <= 0) return;

        const percent = Math.round((scrollTop / docHeight) * 100);

        scrollBuckets.forEach(bucket => {
            if (percent >= bucket && !scrollTracked.has(bucket)) {
                scrollTracked.add(bucket);
                track('scroll', { depth: bucket });
            }
        });
    }

    window.addEventListener('scroll', checkScroll, { passive: true });

    // expose for custom events
    window.beakersTrack = track;
})();

// custom event helpers (call from other scripts)
window.trackQuizSubmit = function(score, total) {
    if (window.beakersTrack) {
        window.beakersTrack('quiz_submit', { score, total, percent: Math.round(score/total*100) });
    }
};

window.trackAudioPlay = function(title) {
    if (window.beakersTrack) {
        window.beakersTrack('audio_play', { title });
    }
};

window.trackSubscribe = function(cadence) {
    if (window.beakersTrack) {
        window.beakersTrack('subscribe', { cadence });
    }
};
