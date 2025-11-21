
/* ==============================
   DOM ELEMENTS (SAFE SELECTORS)
================================= */

/* ==============================
   DOM ELEMENTS (SAFE SELECTORS)
================================= */

const menuBtn = document.getElementById('menu-btn');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const notificationBtn = document.getElementById('notificationBtn');
const notificationDropdown = document.getElementById('notificationDropdown');
const ticketsModal = document.getElementById('bookedTicketsModal');
const accountModal = document.getElementById('accountModal');
const openTicketsModalBtn = document.getElementById('openTicketsModalBtn');
const openAccountModalBtn = document.getElementById('openAccountModalBtn');
const closeTicketsModalBtn = document.querySelector('#bookedTicketsModal .close-btn');
const closeAccountModalBtn = document.querySelector('.account-close');
const logoutBtn = document.getElementById('logoutBtn');
const bookNowBtn = document.getElementById('bookNowBtn');

const chatTab = document.getElementById('chatTab');
const chatWindow = document.getElementById('chatWindow');
const closeChatBtn = document.getElementById('closeChatBtn');
const chatBody = document.getElementById('chatBody');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');

const confirmationModal = document.getElementById('confirmationModal');
const confirmYesBtn = document.getElementById('confirmYesBtn');
const confirmNoBtn = document.getElementById('confirmNoBtn');
const confirmationMessage = document.getElementById('confirmationMessage');
const logoutSuccessModal = document.getElementById('logoutSuccessModal');

let currentConfirmCallback = null;

/* ==============================
   SAFE BOOKINGS PARSE
================================= */

let userBookings = [];
try {
    const el = document.getElementById("bookings-data");
    if (el && el.textContent) {
        userBookings = JSON.parse(el.textContent) || [];
    }
} catch (err) {
    console.warn("Could not parse bookings-data:", err);
    userBookings = [];
}

/* ==============================
   SIDEBAR MENU
================================= */

if (menuBtn && sidebar && overlay) {
    menuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });
}

/* ==============================
   LOGOUT FLOW
================================= */

if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        // Show Confirmation Modal
        if (confirmationModal) {
            confirmationMessage.textContent = "Are you sure you want to logout?";
            confirmationModal.style.display = 'block';
            sidebar.classList.remove('active'); // Close sidebar
            overlay.classList.remove('active');

            // Set callback for YES
            currentConfirmCallback = () => {
                // Perform Logout via AJAX or Redirect
                // For this requirement: "another pop telling him log out successfull"
                // We'll do a fetch to logout, then show success modal.
                fetch("/logout/")
                    .then(() => {
                        confirmationModal.style.display = 'none';
                        if (logoutSuccessModal) {
                            logoutSuccessModal.style.display = 'block';
                        } else {
                            window.location.href = "/users/login/";
                        }
                    })
                    .catch(err => {
                        console.error("Logout failed", err);
                        window.location.href = "/users/login/";
                    });
            };
        } else {
            // Fallback
            if (confirm("Are you sure you want to logout?")) {
                window.location.href = "/logout/";
            }
        }
    });
}

/* ==============================
   NOTIFICATIONS
================================= */

function getNotifications() {
    const stored = localStorage.getItem('userNotifications');
    return stored ? JSON.parse(stored) : [];
}

function saveNotifications(n) {
    localStorage.setItem('userNotifications', JSON.stringify(n));
}

function markNotificationAsRead(i) {
    const n = getNotifications();
    if (n[i]) {
        n[i].read = true;
        saveNotifications(n);
        renderNotifications();
    }
}

function renderNotifications() {
    const notifications = getNotifications();
    const listElement = document.getElementById('notificationList');
    const countElement = document.getElementById('notificationCount');
    if (!listElement || !countElement) return;

    listElement.innerHTML = '';
    let unread = 0;

    if (notifications.length === 0) {
        listElement.innerHTML = '<p class="empty-message">No notifications.</p>';
    }

    notifications.forEach((notification, index) => {
        const item = document.createElement('div');
        item.className = notification.read
            ? 'notification-item-content read'
            : 'notification-item-content unread';

        if (!notification.read) unread++;

        item.innerHTML = `
            <span class="notification-text">${notification.message}</span>
        `;

        const actionButton = document.createElement('button');
        actionButton.className = 'archive-btn';
        actionButton.textContent = notification.read ? 'READ' : 'Mark Read';

        if (notification.read) {
            actionButton.disabled = true;
            actionButton.classList.add('disabled');
        }

        actionButton.addEventListener('click', (e) => {
            e.stopPropagation();
            markNotificationAsRead(index);
        });

        item.appendChild(actionButton);
        listElement.appendChild(item);
    });

    countElement.textContent = unread;
    countElement.style.display = unread > 0 ? 'block' : 'none';
}

function addNotification(msg) {
    const n = getNotifications();
    // Avoid duplicates if the top message is the same
    if (n.length > 0 && n[0].message === msg) return;

    n.unshift({
        message: msg,
        read: false,
        timestamp: new Date().toISOString()
    });
    saveNotifications(n);
    renderNotifications();
}

/* ==============================
   RENDER TICKETS MODAL
================================= */

function renderBookedTickets() {
    const listContainer = document.getElementById("bookedTicketsList");
    if (!listContainer) return;

    listContainer.innerHTML = "";

    if (!userBookings || userBookings.length === 0) {
        listContainer.innerHTML = `<p style="text-align:center;color:#c9a6ff;padding:40px;">
            No tickets booked yet.
        </p>`;
        return;
    }

    userBookings.forEach(b => {
        const item = document.createElement("div");
        item.className = "booking-item";
        item.id = `booking-${b.bookingId || b.id}`; // Add ID for easy removal

        const movie = b.movie || b.movie_name || "Unknown";
        const date = b.date || "";
        const time = b.time || "";
        const seats = b.seats || "";
        const id = b.bookingId || b.id || "";

        item.innerHTML = `
            <div>
                <h4 style="color:#ffcc00;">${movie}</h4>
                <p style="color:#c9a6ff;">
                    🗓️ Date: ${date} at ${time}<br>
                    🪑 Seats: ${seats}<br>
                    #️⃣ ID: ${id}
                </p>
                <form action="/cancel-my-booking/${id}/" method="POST" class="cancel-form">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
                    <button type="submit" class="cancel-btn" style="margin-top: 10px;">Cancel Booking</button>
                </form>
            </div>
        `;

        listContainer.appendChild(item);
    });
}

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/* ==============================
   CHATBOT
================================= */

function toggleChatWindow() {
    if (!chatWindow) return;
    chatWindow.classList.toggle('visible');

    if (chatWindow.classList.contains('visible')) {
        chatInput.focus();
    }
}

function handleUserInput() {
    if (!chatInput || !chatBody) return;

    const userText = chatInput.value.trim();
    if (!userText) return;

    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'chat-message user-message';
    userMessageDiv.textContent = userText;
    chatBody.appendChild(userMessageDiv);
    chatInput.value = '';

    setTimeout(() => {
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'chat-message bot-message';
        botMessageDiv.textContent = "Contact 0712345678 for more info.";
        chatBody.appendChild(botMessageDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }, 500);

    chatBody.scrollTop = chatBody.scrollHeight;
}

/* ==============================
   PAGE INITIALIZATION
================================= */

document.addEventListener("DOMContentLoaded", () => {
    renderNotifications();

    // Check for Django messages and add to notifications
    const messages = document.querySelectorAll('.django-message');
    messages.forEach(msg => {
        addNotification(msg.textContent);
    });

    if (openTicketsModalBtn && ticketsModal) {
        openTicketsModalBtn.addEventListener('click', () => {
            renderBookedTickets();
            ticketsModal.style.display = 'block';
            sidebar?.classList.remove('active');
            overlay?.classList.remove('active');
        });
    }

    if (closeTicketsModalBtn) {
        closeTicketsModalBtn.addEventListener('click', () => {
            ticketsModal.style.display = 'none';
        });
    }

    if (openAccountModalBtn && accountModal) {
        openAccountModalBtn.addEventListener('click', () => {
            accountModal.style.display = 'block';
            sidebar?.classList.remove('active');
            overlay?.classList.remove('active');
        });
    }

    if (closeAccountModalBtn) {
        closeAccountModalBtn.addEventListener('click', () => {
            accountModal.style.display = 'none';
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target === ticketsModal) ticketsModal.style.display = 'none';
        if (event.target === accountModal) accountModal.style.display = 'none';
        if (event.target === confirmationModal) confirmationModal.style.display = 'none';
        if (event.target === logoutSuccessModal) logoutSuccessModal.style.display = 'none';
    });

    if (confirmYesBtn) {
        confirmYesBtn.addEventListener('click', () => {
            if (currentConfirmCallback) currentConfirmCallback();
            // Don't close immediately if it's logout, wait for success modal
            // But for other confirmations, we might want to close.
            // For now, logout callback handles closing.
        });
    }

    if (confirmNoBtn) {
        confirmNoBtn.addEventListener('click', () => {
            if (confirmationModal) confirmationModal.style.display = 'none';
            currentConfirmCallback = null;
        });
    }

    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationDropdown.classList.toggle('show');
        });
    }

    if (bookNowBtn) {
        bookNowBtn.addEventListener("click", () => {
            document.getElementById("movies").scrollIntoView({
                behavior: "smooth"
            });
        });
    }

    if (chatTab) chatTab.addEventListener('click', toggleChatWindow);
    if (closeChatBtn) closeChatBtn.addEventListener('click', toggleChatWindow);
    if (chatSendBtn) chatSendBtn.addEventListener('click', handleUserInput);

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleUserInput();
        });
    }

    // Add default notifications once
    if (getNotifications().length === 0) {
        addNotification("Welcome to Gold Cinema! Book your first ticket to get started.");
        addNotification("Special offer: Get 20% off on your first booking!");
    }
});

/* ==============================
   HELPER
================================= */

function bookMovie(movieName) {
    localStorage.setItem("selectedMovie", movieName);
}

/* ==============================
   ACCOUNT MANAGEMENT MODALS
================================= */

// Get modal elements
const editProfileModal = document.getElementById('editProfileModal');
const changePasswordModal = document.getElementById('changePasswordModal');
const deleteAccountModal = document.getElementById('deleteAccountModal');

// Get button elements
const editAccountBtn = document.getElementById('editAccountBtn');
const changePasswordBtn = document.getElementById('changePasswordBtn');
const deleteAccountBtn = document.getElementById('deleteAccountBtn');

// Get close button elements
const closeEditProfile = document.getElementById('closeEditProfile');
const closeChangePassword = document.getElementById('closeChangePassword');
const closeDeleteAccount = document.getElementById('closeDeleteAccount');
const cancelDelete = document.getElementById('cancelDelete');

// Open Edit Profile Modal
if (editAccountBtn) {
    editAccountBtn.addEventListener('click', () => {
        editProfileModal.style.display = 'block';
        accountModal.style.display = 'none';
    });
}

// Open Change Password Modal
if (changePasswordBtn) {
    changePasswordBtn.addEventListener('click', () => {
        changePasswordModal.style.display = 'block';
        accountModal.style.display = 'none';
    });
}

// Open Delete Account Modal
if (deleteAccountBtn) {
    deleteAccountBtn.addEventListener('click', () => {
        deleteAccountModal.style.display = 'block';
        accountModal.style.display = 'none';
    });
}

// Close Edit Profile Modal
if (closeEditProfile) {
    closeEditProfile.addEventListener('click', () => {
        editProfileModal.style.display = 'none';
    });
}

// Close Change Password Modal
if (closeChangePassword) {
    closeChangePassword.addEventListener('click', () => {
        changePasswordModal.style.display = 'none';
    });
}

// Close Delete Account Modal
if (closeDeleteAccount) {
    closeDeleteAccount.addEventListener('click', () => {
        deleteAccountModal.style.display = 'none';
    });
}

// Cancel Delete
if (cancelDelete) {
    cancelDelete.addEventListener('click', () => {
        deleteAccountModal.style.display = 'none';
    });
}

// Close modals when clicking outside
window.addEventListener('click', (event) => {
    if (event.target === editProfileModal) {
        editProfileModal.style.display = 'none';
    }
    if (event.target === changePasswordModal) {
        changePasswordModal.style.display = 'none';
    }
    if (event.target === deleteAccountModal) {
        deleteAccountModal.style.display = 'none';
    }
});

// Handle Edit Profile Form Submission
const editProfileForm = document.getElementById('editProfileForm');
if (editProfileForm) {
    editProfileForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(editProfileForm);

        try {
            const response = await fetch('/users/update-profile/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                showNotification('success', 'Success', 'Profile updated successfully!');
                editProfileModal.style.display = 'none';
                // Update displayed account info
                document.getElementById('accountFullName').textContent =
                    formData.get('first_name') + ' ' + formData.get('last_name');
                document.getElementById('accountEmail').textContent = formData.get('email');
                document.getElementById('accountPhone').textContent = formData.get('phone') || 'Not provided';
                const location = [formData.get('city'), formData.get('address'), formData.get('zip_code')]
                    .filter(Boolean).join(' ') || 'Not provided';
                document.getElementById('accountLocation').textContent = location;

                // Reload page to reflect changes
                location.reload();
            } else {
                showNotification('error', 'Error', data.error || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('error', 'Error', 'An error occurred while updating your profile');
        }
    });
}

// Handle Change Password Form Submission
const changePasswordForm = document.getElementById('changePasswordForm');
if (changePasswordForm) {
    changePasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(changePasswordForm);
        const newPassword = formData.get('new_password');
        const confirmPassword = formData.get('confirm_password');

        // Validate passwords match
        if (newPassword !== confirmPassword) {
            showNotification('error', 'Error', 'New passwords do not match!');
            return;
        }

        try {
            const response = await fetch('/users/change-password/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                showNotification('success', 'Success', 'Password changed successfully!');
                changePasswordModal.style.display = 'none';
                changePasswordForm.reset();
            } else {
                showNotification('error', 'Error', data.error || 'Failed to change password');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('error', 'Error', 'An error occurred while changing your password');
        }
    });
}

// Handle Delete Account Form Submission
const deleteAccountForm = document.getElementById('deleteAccountForm');
if (deleteAccountForm) {
    deleteAccountForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(deleteAccountForm);

        // Final confirmation
        const confirmed = confirm('This action is PERMANENT and cannot be undone. Are you absolutely sure you want to delete your account?');
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch('/users/delete-account/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                showNotification('success', 'Account Deleted', 'Your account has been deleted. You will now be redirected to the login page.');
                setTimeout(() => {
                    window.location.href = '/users/login/';
                }, 2000);
            } else {
                showNotification('error', 'Error', data.error || 'Failed to delete account. Please check your password.');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('error', 'Error', 'An error occurred while deleting your account');
        }
    });
}
