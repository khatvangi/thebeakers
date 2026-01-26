#!/usr/bin/env node
/**
 * notebooklm_auth.js - authenticate with Google for NotebookLM automation
 *
 * run this once to save your login session:
 *   node scripts/notebooklm_auth.js
 *
 * this will:
 * 1. open a visible browser window
 * 2. navigate to NotebookLM (triggers Google login)
 * 3. wait for you to log in manually
 * 4. save the session to .playwright-auth/ for future automation
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const AUTH_DIR = path.join(__dirname, '..', '.playwright-auth');
const STATE_FILE = path.join(AUTH_DIR, 'google-session.json');

async function authenticate() {
    console.log('🔐 NotebookLM Authentication Setup\n');

    // ensure auth directory exists
    if (!fs.existsSync(AUTH_DIR)) {
        fs.mkdirSync(AUTH_DIR, { recursive: true });
    }

    console.log('1. Launching browser (visible window)...');

    const browser = await chromium.launch({
        headless: false,
        slowMo: 100  // slow down for visibility
    });

    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('2. Navigating to NotebookLM...');
    await page.goto('https://notebooklm.google.com');

    console.log('\n========================================');
    console.log('   Please log in to Google in the browser window');
    console.log('   The script will wait until you reach NotebookLM');
    console.log('========================================\n');

    // wait for successful login - check for NotebookLM main page
    try {
        await page.waitForURL('**/notebooklm.google.com/**', {
            timeout: 300000  // 5 minutes to log in
        });

        // wait a bit more for page to fully load
        await page.waitForTimeout(3000);

        console.log('3. Login detected! Saving session...');

        // save the session state
        const state = await context.storageState();
        fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));

        console.log(`\n✅ Session saved to: ${STATE_FILE}`);
        console.log('   You can now close the browser.\n');

        // take a screenshot as proof
        await page.screenshot({ path: path.join(AUTH_DIR, 'logged-in.png') });
        console.log('   Screenshot saved to: .playwright-auth/logged-in.png');

    } catch (err) {
        console.error('\n❌ Login timed out or failed:', err.message);
        console.log('   Please try again.');
    }

    // keep browser open briefly so user can see success
    await page.waitForTimeout(5000);
    await browser.close();

    console.log('\n🎉 Done! Claude can now automate NotebookLM.');
}

// check if already authenticated
async function checkExisting() {
    if (fs.existsSync(STATE_FILE)) {
        console.log('Found existing session at:', STATE_FILE);
        console.log('Testing if still valid...\n');

        const browser = await chromium.launch({ headless: true });
        const context = await browser.newContext({
            storageState: STATE_FILE
        });
        const page = await context.newPage();

        try {
            await page.goto('https://notebooklm.google.com');
            await page.waitForTimeout(3000);

            const url = page.url();
            if (url.includes('accounts.google.com')) {
                console.log('❌ Session expired. Re-authenticating...\n');
                await browser.close();
                return false;
            } else {
                console.log('✅ Session still valid! No action needed.');
                await browser.close();
                return true;
            }
        } catch (e) {
            console.log('❌ Error checking session:', e.message);
            await browser.close();
            return false;
        }
    }
    return false;
}

async function main() {
    const stillValid = await checkExisting();
    if (!stillValid) {
        await authenticate();
    }
}

main().catch(console.error);
