const API = (window.APP_CONFIG?.API_BASE_URL || '') + '/api';
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const toast = (message) => {
    const el = $('#toast');
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.remove('show'), 3500);
};

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[c]));
}

async function api(path, options = {}) {
    const headers = {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {})
    };
    const response = await fetch(API + path, {
        credentials: 'same-origin',
        ...options,
        headers
    });
    const type = response.headers.get('content-type') || '';
    if (!response.ok) {
        let data = {};
        if (type.includes('json')) {
            data = await response.json().catch(() => ({}));
        }
        throw new Error(data.error || data.message || `Request failed (${response.status})`);
    }
    return type.includes('json') ? response.json() : response.blob();
}

// Set dynamic year in footer
const yearEl = $('#year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Mobile navigation toggle
const menuToggle = $('#menuToggle');
const mainNav = $('#mainNav');
if (menuToggle && mainNav) {
    menuToggle.addEventListener('click', () => mainNav.classList.toggle('open'));
    $$('#mainNav a').forEach(a => a.addEventListener('click', () => mainNav.classList.remove('open')));
}

// Vehicle quick booking buttons
$$('.book-vehicle').forEach(button => {
    button.addEventListener('click', () => {
        const vehicleSelect = $('#vehicleSelect');
        if (vehicleSelect && button.dataset.vehicle) {
            vehicleSelect.value = button.dataset.vehicle;
        }
        const bookingSection = $('#booking');
        if (bookingSection) {
            bookingSection.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Set minimum booking date to today
const dateInput = $('#bookingForm [name="travel_date"]');
if (dateInput) {
    dateInput.min = new Date().toISOString().slice(0, 10);
}

// Booking Form submission
const bookingForm = $('#bookingForm');
if (bookingForm) {
    bookingForm.addEventListener('submit', async event => {
        event.preventDefault();
        const form = event.currentTarget;
        const button = $('.submit-btn', form);
        const message = $('#bookingMessage');

        message.textContent = '';
        message.className = 'form-message';
        button.classList.add('is-loading');
        button.disabled = true;

        const data = Object.fromEntries(new FormData(form).entries());
        data.passengers = Number(data.passengers) || 1;

        try {
            const result = await api('/bookings', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            message.className = 'form-message success';
            message.textContent = `${result.message} Booking ID: ${result.booking_id}. Please keep this for your records.`;
            form.reset();
            if (dateInput) dateInput.min = new Date().toISOString().slice(0, 10);
            toast('Booking request submitted successfully!');
        } catch (error) {
            message.className = 'form-message error';
            message.textContent = error.message;
            toast(error.message);
        } finally {
            button.classList.remove('is-loading');
            button.disabled = false;
        }
    });
}

// Contact Enquiry Form submission
const contactForm = $('#contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', async event => {
        event.preventDefault();
        const form = event.currentTarget;
        const button = $('button[type="submit"]', form);
        const messageEl = $('#contactMessage');
        const d = Object.fromEntries(new FormData(form).entries());

        button.disabled = true;
        messageEl.textContent = 'Saving your enquiry...';
        messageEl.className = 'form-message';

        try {
            await api('/inquiries', {
                method: 'POST',
                body: JSON.stringify(d)
            });
            const waNumber = window.APP_CONFIG?.WHATSAPP_NUMBER || '919696299353';
            const body = `Hello Mangalore Taxi Corporation,\nName: ${d.name}\nContact: ${d.contact}\nMessage: ${d.message}`;
            const url = `https://wa.me/${waNumber}?text=${encodeURIComponent(body)}`;

            messageEl.className = 'form-message success';
            messageEl.textContent = 'Enquiry received! Connecting you to WhatsApp...';
            window.open(url, '_blank', 'noopener');
            form.reset();
            toast('Enquiry sent successfully!');
        } catch (error) {
            messageEl.className = 'form-message error';
            messageEl.textContent = error.message;
            toast(error.message);
        } finally {
            button.disabled = false;
        }
    });
}

// Load testimonials / reviews
async function loadReviews() {
    try {
        const { reviews } = await api('/reviews');
        if (!reviews?.length) return;
        const reviewGrid = $('#reviewGrid');
        if (!reviewGrid) return;

        reviewGrid.innerHTML = reviews.map(r => `
            <article class="review-card">
                <div class="stars">${'★'.repeat(Math.max(0, Math.min(5, Number(r.rating) || 5)))}</div>
                <p>“${escapeHtml(r.comment || 'Thank you for travelling with us.')}”</p>
                <b>${escapeHtml(r.name || 'Customer')}</b>
                <small>Verified review</small>
            </article>
        `).join('');
    } catch (_) {
        // Fallback reviews in HTML remain displayed if fetch fails
    }
}

loadReviews();
