// Main JavaScript file for the Accounting System
document.addEventListener('DOMContentLoaded', function() {
    console.log('Accounting System initialized');
});

const { createApp } = Vue

const app = createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            isAuthenticated: false,
            showLogin: true,
            showNewProjectModal: false,
            user: null,
            projects: [],
            loginForm: {
                email: '',
                password: ''
            },
            signupForm: {
                username: '',
                email: '',
                password: ''
            },
            newProject: {
                name: '',
                description: ''
            }
        }
    },
    methods: {
        async checkAuth() {
            try {
                const response = await axios.get('/api/user/profile')
                this.user = response.data
                this.isAuthenticated = true
                this.loadProjects()
            } catch (error) {
                this.isAuthenticated = false
            }
        },
        async login() {
            try {
                await axios.post('/auth/login', this.loginForm)
                await this.checkAuth()
                this.loginForm = { email: '', password: '' }
            } catch (error) {
                alert(error.response?.data?.error || 'Login failed')
            }
        },
        async signup() {
            try {
                await axios.post('/auth/signup', this.signupForm)
                await this.checkAuth()
                this.signupForm = { username: '', email: '', password: '' }
            } catch (error) {
                alert(error.response?.data?.error || 'Signup failed')
            }
        },
        async logout() {
            try {
                await axios.get('/auth/logout')
                this.isAuthenticated = false
                this.user = null
            } catch (error) {
                alert(error.response?.data?.error || 'Logout failed')
            }
        },
        async forgotPassword() {
            const email = prompt('Please enter your email address:')
            if (email) {
                try {
                    await axios.post('/auth/reset-password', { email })
                    alert('Password reset email has been sent')
                } catch (error) {
                    alert(error.response?.data?.error || 'Failed to send reset email')
                }
            }
        },
        async loadProjects() {
            try {
                const response = await axios.get('/api/projects/')
                this.projects = await Promise.all(response.data.map(async project => {
                    const summary = await this.getProjectSummary(project.id)
                    return { ...project, summary }
                }))
            } catch (error) {
                alert(error.response?.data?.error || 'Failed to load projects')
            }
        },
        async createProject() {
            try {
                await axios.post('/api/projects/', this.newProject)
                this.showNewProjectModal = false
                this.newProject = { name: '', description: '' }
                await this.loadProjects()
            } catch (error) {
                alert(error.response?.data?.error || 'Failed to create project')
            }
        },
        async getProjectSummary(projectId) {
            try {
                const response = await axios.get(`/api/transactions/${projectId}/summary`)
                return response.data
            } catch (error) {
                console.error('Failed to load project summary:', error)
                return null
            }
        },
        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString()
        },
        formatMoney(amount) {
            return amount.toFixed(2)
        },
        viewProject(project) {
            // TODO: Implement project detail view
            alert('Project detail view coming soon!')
        }
    },
    mounted() {
        this.checkAuth()
    }
})

app.mount('#app')
