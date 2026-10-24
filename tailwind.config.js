/** Configuração do Tailwind CSS (build local via build_css.py) */
module.exports = {
    content: ['./index.html', './js/**/*.js'],
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
            colors: {
                darkBg: '#0D0F12',
                cardBg: '#1A1D24',
                cardHover: '#222630',
                accentGreen: '#10B981',
                accentRed: '#EF4444',
                accentBlue: '#3B82F6',
                accentPurple: '#8B5CF6'
            }
        }
    },
    plugins: []
};
