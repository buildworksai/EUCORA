/** @type {import('tailwindcss').Config} */
export default {
	darkMode: ['class'],
	content: [
		'./index.html',
		'./src/**/*.{js,ts,jsx,tsx}',
	],
	theme: {
		extend: {
			colors: {
				eucora: {
					// Start BuildWorks.AI Branding
					deepBlue: {
						DEFAULT: '#1565C0',
						dark: '#0D47A1'
					},
					teal: {
						DEFAULT: '#00ACC1',
						dark: '#0097A7'
					},
					gold: {
						DEFAULT: '#FF8F00',
						dark: '#F57C00'
					},
					green: {
						DEFAULT: '#388E3C',
						dark: '#2E7D32'
					},
					// End BuildWorks.AI Branding
					red: '#E74C3C', // Keep for destructive if needed, or map to error
					gray: {
						'50': '#F8F9FA',
						'100': '#E9ECEF',
						'200': '#DEE2E6',
						'300': '#CED4DA',
						'400': '#ADB5BD',
						'500': '#6C757D',
						'600': '#495057',
						'700': '#343A40',
						'800': '#212529',
						'900': '#0D1117'
					}
				},
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))'
				}
			},
			backdropBlur: {
				xs: '2px'
			},
			animation: {
				'fade-in': 'fadeIn 0.3s ease-in-out',
				'slide-up': 'slideUp 0.4s ease-out',
				'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
			},
			keyframes: {
				fadeIn: {
					'0%': {
						opacity: 0
					},
					'100%': {
						opacity: 1
					}
				},
				slideUp: {
					'0%': {
						transform: 'translateY(20px)',
						opacity: 0
					},
					'100%': {
						transform: 'translateY(0)',
						opacity: 1
					}
				}
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			}
		}
	},
	plugins: [require('tailwindcss-animate')],
}
