const $ = s => document.querySelector(s);
const loginPanel = $('#loginPanel');
const dashboard = $('#dashboard');
let bookings = [];
let inquiries = [];

function esc(v) {
    return String(v ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[c]));
}

async function api(path, options = {}) {
    const res = await fetch('/api' + path, {
        credentials: 'same-origin',
        ...options,
        headers: {
            ...(options.body ? { 'Content-Type': 'application/json' } : {}),
            ...(options.headers || {})
        }
    });
    const type = res.headers.get('content-type') || '';
    if (!res.ok) {
        const data = type.includes('json') ? await res.json().catch(() => ({})) : {};
        throw new Error(data.error || `Request failed (${res.status})`);
    }
    return type.includes('json') ? res.json() : res.blob();
}

function showDashboard(username) {
    loginPanel.classList.add('hidden');
    dashboard.classList.remove('hidden');
    $('#adminEmail').textContent = username || 'Administrator';
    refresh();
}

// Login
$('#loginForm').addEventListener('submit', async e => {
    e.preventDefault();
    const b = $('button', e.currentTarget);
    b.disabled = true;
    $('#loginMessage').textContent = 'Signing in...';
    const d = Object.fromEntries(new FormData(e.currentTarget));
    try {
        const r = await api('/admin/login', { method: 'POST', body: JSON.stringify(d) });
        showDashboard(r.username || r.email);
    } catch (err) {
        $('#loginMessage').textContent = err.message;
    } finally {
        b.disabled = false;
    }
});

// Refresh Dashboard Data
async function refresh() {
    try {
        const [b, i] = await Promise.all([
            api('/admin/bookings'),
            api('/admin/inquiries')
        ]);
        bookings = b.bookings || [];
        inquiries = i.inquiries || [];

        $('#totalBookings').textContent = bookings.length;
        $('#pendingBookings').textContent = bookings.filter(x => x.status === 'Pending').length;
        $('#confirmedBookings').textContent = bookings.filter(x => x.status === 'Confirmed').length;
        $('#totalInquiries').textContent = inquiries.length;

        renderBookings();
        renderInquiries();
    } catch (e) {
        $('#dashboardMessage').textContent = e.message;
    }
}

// Render Bookings Table
function renderBookings() {
    const q = ($('#bookingSearch').value || '').toLowerCase();
    const rows = bookings.filter(b =>
        [b.booking_id, b.customer_name, b.phone, b.pickup, b.drop, b.vehicle, b.status]
            .some(v => String(v || '').toLowerCase().includes(q))
    );

    const tbody = $('#bookingRows');
    if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="8">No bookings found.</td></tr>';
        return;
    }

    tbody.innerHTML = rows.map(b => {
        const extraNotes = [b.luggage ? `Luggage: ${esc(b.luggage)}` : '', b.special_instructions ? `Note: ${esc(b.special_instructions)}` : ''].filter(Boolean).join(' | ');
        return `
            <tr>
                <td><b>${esc(b.booking_id)}</b></td>
                <td>
                    ${esc(b.customer_name)}<br>
                    <small>${esc(b.phone)}${b.email ? '<br>' + esc(b.email) : ''}</small>
                </td>
                <td>
                    ${esc(b.pickup)} → ${esc(b.drop)}<br>
                    <small>${esc(b.trip_type)}</small>
                </td>
                <td>
                    ${esc(b.travel_date)}<br>
                    <small>${esc(b.pickup_time)}</small>
                </td>
                <td>${esc(b.vehicle)}</td>
                <td>${esc(b.passengers || 1)}</td>
                <td>
                    <select class="status-select" data-id="${esc(b.booking_id)}">
                        ${['Pending', 'Confirmed', 'Completed', 'Cancelled'].map(s => 
                            `<option value="${s}" ${b.status === s ? 'selected' : ''}>${s}</option>`
                        ).join('')}
                    </select>
                    ${extraNotes ? `<br><small style="color:#718091;">${extraNotes}</small>` : ''}
                </td>
                <td>
                    <button class="delete-btn" data-id="${esc(b.booking_id)}" style="background:#e55353;color:#fff;border:none;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:11px;">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Render Inquiries List
function renderInquiries() {
    const q = ($('#inquirySearch').value || '').toLowerCase();
    const list = inquiries.filter(x =>
        [x.name, x.contact, x.message].some(v => String(v || '').toLowerCase().includes(q))
    );

    const container = $('#inquiryList');
    if (!list.length) {
        container.innerHTML = '<p class="muted">No enquiries found.</p>';
        return;
    }

    container.innerHTML = list.map(x => `
        <article class="inquiry">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h3>${esc(x.name)}</h3>
                <small>${esc(x.created_at ? new Date(x.created_at).toLocaleString() : '')}</small>
            </div>
            <p><strong>Contact:</strong> ${esc(x.contact)}</p>
            <p style="background:#f8fafc;padding:10px;border-radius:6px;margin:8px 0;">${esc(x.message)}</p>
        </article>
    `).join('');
}

// Status update listener
$('#bookingRows').addEventListener('change', async e => {
    if (!e.target.matches('select.status-select')) return;
    const bookingId = e.target.dataset.id;
    const newStatus = e.target.value;
    try {
        await api('/admin/bookings/' + encodeURIComponent(bookingId), {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus })
        });
        $('#dashboardMessage').textContent = `Booking ${bookingId} updated to ${newStatus}.`;
        refresh();
    } catch (err) {
        $('#dashboardMessage').textContent = err.message;
    }
});

// Delete booking listener
$('#bookingRows').addEventListener('click', async e => {
    if (!e.target.matches('.delete-btn')) return;
    const bookingId = e.target.dataset.id;
    if (!confirm(`Are you sure you want to delete booking ${bookingId}? This cannot be undone.`)) return;

    try {
        await api('/admin/bookings/' + encodeURIComponent(bookingId), {
            method: 'DELETE'
        });
        $('#dashboardMessage').textContent = `Booking ${bookingId} has been deleted.`;
        refresh();
    } catch (err) {
        $('#dashboardMessage').textContent = err.message;
    }
});

// Search inputs
$('#bookingSearch').addEventListener('input', renderBookings);
$('#inquirySearch').addEventListener('input', renderInquiries);

// Tab switching
document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x === t));
        $('#bookingsView').classList.toggle('hidden', t.dataset.tab !== 'bookings');
        $('#inquiriesView').classList.toggle('hidden', t.dataset.tab !== 'inquiries');
    });
});

// Logout
$('#logoutBtn').addEventListener('click', async () => {
    try {
        await api('/admin/logout', { method: 'POST' });
    } finally {
        dashboard.classList.add('hidden');
        loginPanel.classList.remove('hidden');
    }
});

// Export Excel
$('#exportBtn').addEventListener('click', async () => {
    try {
        const blob = await api('/admin/export');
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'MTC_Bookings.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        $('#dashboardMessage').textContent = e.message;
    }
});

// Check existing session on page load
(async () => {
    try {
        const me = await api('/admin/me');
        if (me.authenticated) {
            showDashboard(me.username || me.email);
        }
    } catch (_) {}
})();
