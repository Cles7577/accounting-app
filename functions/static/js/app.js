// State management
let currentUser = null;
let isAuthenticated = false;

// API endpoints
const API = {
    login: '/api/login',
    register: '/api/register',
    dashboard: '/api/dashboard',
    createTeam: '/api/create-team',
    newProject: '/api/new-project'
};

// Update navigation based on auth state
function updateNavigation() {
    const navButtons = document.getElementById('navButtons');
    navButtons.innerHTML = '';

    if (isAuthenticated) {
        navButtons.innerHTML = `
            <button onclick="loadDashboard()" class="mx-2 px-4 py-2 text-gray-600 hover:text-gray-900">Dashboard</button>
            <button onclick="logout()" class="mx-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">Logout</button>
        `;
    } else {
        navButtons.innerHTML = `
            <button onclick="showLoginForm()" class="mx-2 px-4 py-2 text-gray-600 hover:text-gray-900">Login</button>
            <button onclick="showRegisterForm()" class="mx-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Register</button>
        `;
    }
}

// Show login form
function showLoginForm() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="min-h-[80vh] flex items-center justify-center">
            <div class="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
                <h2 class="text-2xl font-bold mb-6 text-center">Login</h2>
                <form onsubmit="handleLogin(event)" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Email</label>
                        <input type="email" name="email" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Password</label>
                        <input type="password" name="password" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
                        Login
                    </button>
                </form>
            </div>
        </div>
    `;
}

// Show registration form
function showRegisterForm() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="min-h-[80vh] flex items-center justify-center">
            <div class="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
                <h2 class="text-2xl font-bold mb-6 text-center">Register</h2>
                <form onsubmit="handleRegister(event)" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Email</label>
                        <input type="email" name="email" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Username</label>
                        <input type="text" name="username" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Password</label>
                        <input type="password" name="password" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
                        Register
                    </button>
                </form>
            </div>
        </div>
    `;
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        email: formData.get('email'),
        password: formData.get('password')
    };

    try {
        const response = await fetch(API.login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const result = await response.json();
            currentUser = result.user;
            isAuthenticated = true;
            updateNavigation();
            loadDashboard();
        } else {
            alert('Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login.');
    }
}

// Handle registration
async function handleRegister(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        email: formData.get('email'),
        username: formData.get('username'),
        password: formData.get('password')
    };

    try {
        const response = await fetch(API.register, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Registration successful! Please login.');
            showLoginForm();
        } else {
            alert('Registration failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred during registration.');
    }
}

// Load dashboard
async function loadDashboard() {
    if (!isAuthenticated) {
        showLoginForm();
        return;
    }

    try {
        const response = await fetch(API.dashboard);
        if (response.ok) {
            const data = await response.json();
            displayDashboard(data);
        } else {
            throw new Error('Failed to load dashboard');
        }
    } catch (error) {
        console.error('Dashboard error:', error);
        alert('Failed to load dashboard');
    }
}

// Display dashboard
function displayDashboard(data) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h2 class="text-2xl font-bold">Dashboard</h2>
                <button onclick="showNewProjectForm()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                    New Project
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                ${data.projects ? data.projects.map(project => `
                    <div class="bg-white p-6 rounded-xl shadow-lg">
                        <h3 class="text-xl font-semibold mb-2">${project.name}</h3>
                        <p class="text-gray-600 mb-4">${project.description}</p>
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500">Budget: $${project.budget}</span>
                            <button onclick="viewProject(${project.id})" class="text-blue-500 hover:text-blue-600">
                                View Details
                            </button>
                        </div>
                    </div>
                `).join('') : '<p>No projects found.</p>'}
            </div>
        </div>
    `;
}

// Logout
function logout() {
    currentUser = null;
    isAuthenticated = false;
    updateNavigation();
    showLoginForm();
}

// Initialize app
function init() {
    updateNavigation();
    showLoginForm();
}

// Start the app
init();
