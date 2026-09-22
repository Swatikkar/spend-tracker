const API_BASE = "http://127.0.0.1:8000";
let token = localStorage.getItem("token");


document.getElementById("toggleRegister").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("registerForm").style.display = "block";
});

document.getElementById("toggleLogin").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("registerForm").style.display = "none";
    document.getElementById("loginForm").style.display = "block";
});

function showAuthMessage(message, isError = false) {
    const msgEl = document.getElementById("authMessage");
    msgEl.textContent = message;
    msgEl.className = isError ? "message error" : "message success";
}

function showFormMessage(message, isError = false) {
    const msgEl = document.getElementById("formMessage");
    msgEl.textContent = message;
    msgEl.className = isError ? "message error" : "message success";
}

async function register(email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            showAuthMessage(data.detail || "Registration failed", true);
            return;
        }

        showAuthMessage("Registration successful! Please login.", false);
        document.getElementById("registerForm").reset();
        setTimeout(() => {
            document.getElementById("registerForm").style.display = "none";
            document.getElementById("loginForm").style.display = "block";
        }, 1000);
    } catch (error) {
        showAuthMessage("Error: " + error.message, true);
    }
}

async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            showAuthMessage(data.detail || "Login failed", true);
            return;
        }

        token = data.access_token;
        localStorage.setItem("token", token);
        document.getElementById("loginForm").reset();
        showAuthSection(false);
        loadSummary();
        loadExpenses();
    } catch (error) {
        showAuthMessage("Error: " + error.message, true);
    }
}

function logout() {
    token = null;
    localStorage.removeItem("token");
    document.getElementById("loginForm").reset();
    document.getElementById("registerForm").reset();
    showAuthSection(true);
}


function showAuthSection(show) {
    document.getElementById("authSection").style.display = show ? "block" : "none";
    document.getElementById("appSection").style.display = show ? "none" : "block";
}


async function apiCall(endpoint, method = "GET", body = null) {
    const options = {
        method,
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);

    if (response.status === 401) {
        logout();
        throw new Error("Session expired. Please login again.");
    }

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "API error");
    }

    return response.json();
}

async function addExpense(amount, category, note, date) {
    try {
        await apiCall("/expenses", "POST", {
            amount: parseFloat(amount),
            category,
            note: note || null,
            date
        });

        showFormMessage("Expense added successfully!", false);
        document.getElementById("expenseForm").reset();
        
        setTimeout(() => {
            loadExpenses();
            loadSummary();
        }, 500);
    } catch (error) {
        showFormMessage(error.message, true);
    }
}

async function loadExpenses(category = null, startDate = null, endDate = null) {
    try {
        let url = "/expenses?";
        if (category) url += `category=${encodeURIComponent(category)}&`;
        if (startDate) url += `start_date=${startDate}&`;
        if (endDate) url += `end_date=${endDate}&`;

        const expenses = await apiCall(url.slice(0, -1));

        if (expenses.length === 0) {
            document.getElementById("expenseListContainer").innerHTML = "<p class='info'>No expenses found.</p>";
            return;
        }

        let html = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Category</th>
                        <th>Note</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
        `;

        expenses.forEach(expense => {
            html += `
                <tr>
                    <td>${expense.date}</td>
                    <td>${expense.category}</td>
                    <td>${expense.note || "-"}</td>
                    <td>₹${parseFloat(expense.amount).toFixed(2)}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        document.getElementById("expenseListContainer").innerHTML = html;
    } catch (error) {
        document.getElementById("expenseListContainer").innerHTML = `<p class='info'>No expenses found.</p>`;
    }
}

async function loadSummary(month = null) {
    try {
        let url = "/summary";
        if (month) url += `?month=${month}`;

        const summary = await apiCall(url);

        let html = `
            <div class="summary-info">
                <p><strong>Month:</strong> ${summary.month}</p>
                <p><strong>Total Spend:</strong> ₹${parseFloat(summary.total_spend).toFixed(2)}</p>
                <p><strong>Previous Month:</strong> ₹${parseFloat(summary.previous_month_total).toFixed(2)}</p>
        `;

        if (summary.month_over_month_change_percentage !== null) {
            const change = summary.month_over_month_change_percentage;
            const changeClass = change >= 0 ? "increase" : "decrease";
            html += `<p class="${changeClass}"><strong>Change:</strong> ${change.toFixed(2)}%</p>`;
        } else {
            html += `<p><strong>Change:</strong> No previous data</p>`;
        }

        html += `
                <h3>Spending by Category:</h3>
        `;

        if (Object.keys(summary.spend_by_category).length === 0) {
            html += `<p>No expenses this month.</p>`;
        } else {
            html += `<ul>`;
            Object.entries(summary.spend_by_category).forEach(([category, amount]) => {
                html += `<li>${category}: ₹${parseFloat(amount).toFixed(2)}</li>`;
            });
            html += `</ul>`;
        }

        if (summary.insights.length > 0) {
            html += `<h3>Insights:</h3><ul>`;
            summary.insights.forEach(insight => {
                html += `<li>${insight}</li>`;
            });
            html += `</ul>`;
        }

        html += `</div>`;

        document.getElementById("summaryContainer").innerHTML = html;
    } catch (error) {
        document.getElementById("summaryContainer").innerHTML = `<p class="info">No expenses added yet for this month.</p>`;
    }
}


document.getElementById("loginForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    login(email, password);
});

document.getElementById("registerForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;
    register(email, password);
});

document.getElementById("expenseForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const amount = document.getElementById("amount").value;
    const category = document.getElementById("category").value;
    const note = document.getElementById("note").value;
    const date = document.getElementById("date").value;
    addExpense(amount, category, note, date);
});

document.getElementById("filterBtn").addEventListener("click", () => {
    const category = document.getElementById("filterCategory").value || null;
    const startDate = document.getElementById("filterStartDate").value || null;
    const endDate = document.getElementById("filterEndDate").value || null;
    loadExpenses(category, startDate, endDate);
});

document.getElementById("clearFilterBtn").addEventListener("click", () => {
    document.getElementById("filterCategory").value = "";
    document.getElementById("filterStartDate").value = "";
    document.getElementById("filterEndDate").value = "";
    loadExpenses();
});

document.getElementById("logoutBtn").addEventListener("click", logout);


if (token) {
    showAuthSection(false);
    loadSummary();
    loadExpenses();
} else {
    showAuthSection(true);
}