// Глобальные переменные
let currentUser = null;
let authToken = localStorage.getItem('authToken');

// API базовый URL
const API_BASE = '/api';

// Настройка HTTP клиента
class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                this.logout();
                return;
            }

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Произошла ошибка');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    logout() {
        localStorage.removeItem('authToken');
        authToken = null;
        window.location.href = '/login';
    }
}

const api = new ApiClient(API_BASE);

// Утилиты
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Ищем контейнер для уведомлений или создаем его
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        document.body.insertBefore(alertContainer, document.body.firstChild);
    }
    
    alertContainer.appendChild(alertDiv);
    
    // Автоматически удаляем уведомление через 5 секунд
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPhone(phone) {
    // Простое форматирование телефона
    if (phone.length === 11 && phone.startsWith('7')) {
        return `+7 (${phone.slice(1, 4)}) ${phone.slice(4, 7)}-${phone.slice(7, 9)}-${phone.slice(9)}`;
    }
    return phone;
}

// Модальные окна
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Закрытие модальных окон по клику вне них
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Аутентификация
async function login(email, password) {
    try {
        const response = await api.post('/auth/login-json', {
            email: email,
            password: password
        });
        
        authToken = response.access_token;
        localStorage.setItem('authToken', authToken);
        
        showAlert('Вход выполнен успешно!', 'success');
        window.location.href = '/dashboard';
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function register(userData) {
    try {
        await api.post('/auth/register', userData);
        showAlert('Регистрация прошла успешно! Теперь вы можете войти.', 'success');
        window.location.href = '/login';
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    window.location.href = '/login';
}

// Проверка аутентификации
function checkAuth() {
    if (!authToken) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем аутентификацию на защищенных страницах
    const protectedPages = ['/dashboard', '/clients', '/appointments', '/services'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.includes(currentPath) && !authToken) {
        window.location.href = '/login';
        return;
    }
    
    // Если пользователь авторизован и находится на странице входа/регистрации
    if (authToken && (currentPath === '/login' || currentPath === '/register')) {
        window.location.href = '/dashboard';
        return;
    }
    
    // Инициализируем страницу в зависимости от текущего пути
    switch (currentPath) {
        case '/dashboard':
            initDashboard();
            break;
        case '/clients':
            initClients();
            break;
        case '/appointments':
            initAppointments();
            break;
        case '/services':
            initServices();
            break;
    }
});

// Функции инициализации страниц (будут определены в отдельных файлах)
function initDashboard() {
    if (!checkAuth()) return;
    loadDashboardStats();
}

function initClients() {
    if (!checkAuth()) return;
    loadClients();
}

function initAppointments() {
    if (!checkAuth()) return;
    loadAppointments();
    loadServices();
    loadClients();
}

function initServices() {
    if (!checkAuth()) return;
    loadServices();
}

// Загрузка данных дашборда
async function loadDashboardStats() {
    try {
        const stats = await api.get('/dashboard/stats');
        
        // Обновляем статистику
        document.getElementById('totalClients').textContent = stats.total_clients;
        document.getElementById('totalAppointments').textContent = stats.total_appointments;
        document.getElementById('todayAppointments').textContent = stats.today_appointments;
        document.getElementById('upcomingAppointments').textContent = stats.upcoming_appointments;
        
        // Загружаем последние записи
        loadRecentAppointments();
    } catch (error) {
        showAlert('Ошибка загрузки статистики: ' + error.message, 'error');
    }
}

async function loadRecentAppointments() {
    try {
        const appointments = await api.get('/appointments?limit=5');
        const tbody = document.getElementById('recentAppointments');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        appointments.forEach(appointment => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${appointment.client.full_name}</td>
                <td>${appointment.service.name}</td>
                <td>${formatDate(appointment.datetime)}</td>
                <td>
                    <span class="badge badge-${getStatusColor(appointment.status)}">
                        ${getStatusText(appointment.status)}
                    </span>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Ошибка загрузки записей:', error);
    }
}

function getStatusColor(status) {
    const colors = {
        'scheduled': 'primary',
        'confirmed': 'success',
        'completed': 'secondary',
        'cancelled': 'danger',
        'no_show': 'warning'
    };
    return colors[status] || 'secondary';
}

function getStatusText(status) {
    const texts = {
        'scheduled': 'Запланирована',
        'confirmed': 'Подтверждена',
        'completed': 'Выполнена',
        'cancelled': 'Отменена',
        'no_show': 'Не явился'
    };
    return texts[status] || status;
}