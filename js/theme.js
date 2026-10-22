// theme.js - Gerenciamento de Tema (Dark / Light Mode)

const THEME_KEY = 'fincontrol_theme';

function initTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme ? savedTheme : (prefersDark ? 'dark' : 'dark'); // Padrão: dark conforme especificado
    setTheme(initialTheme);
}

function setTheme(theme) {
    const html = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');
    
    if (theme === 'dark') {
        html.classList.add('dark');
        localStorage.setItem(THEME_KEY, 'dark');
        if (themeIcon) {
            themeIcon.className = 'fa-solid fa-sun text-amber-400';
            themeIcon.parentElement.title = 'Alternar para Modo Claro';
        }
    } else {
        html.classList.remove('dark');
        localStorage.setItem(THEME_KEY, 'light');
        if (themeIcon) {
            themeIcon.className = 'fa-solid fa-moon text-slate-600 dark:text-slate-300';
            themeIcon.parentElement.title = 'Alternar para Modo Escuro';
        }
    }

    // Dispara evento customizado para permitir que gráficos e componentes ajustem cores
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    setTheme(isDark ? 'light' : 'dark');
}

// Inicializa o tema o mais cedo possível
initTheme();

