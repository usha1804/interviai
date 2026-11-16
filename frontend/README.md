# InterviAI Frontend

React + Vite + Tailwind CSS frontend for the InterviAI interview preparation platform.

## Overview

Modern, responsive single-page application for practicing interviews with AI-generated questions, real-time feedback, and comprehensive analytics.

## Features

- 🎯 Interactive interview sessions
- 🤖 AI-generated questions and feedback
- 📊 Real-time performance analytics
- ✨ Responsive SaaS workspace with a reusable sidebar and top navigation
- 📈 Light design system with shared cards, page headers, and empty states
- 🧭 Searchable navigation, account menu, and mobile sidebar drawer
- 📱 Fully responsive design
- ⚡ Fast development with Vite
- 🎨 Beautiful UI with Tailwind CSS
- 🔐 Protected routes with authentication

## Tech Stack

- **Framework**: React 18
- **Bundler**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **State Management**: Context API + Hooks
- **Charts**: Recharts
- **Icons**: Lucide React

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Development Server

```bash
npm run dev
```

Application will be available at `http://localhost:5173`

## Available Scripts

```bash
# Development
npm run dev              # Start dev server
npm run dev:host        # Accessible from network

# Production
npm run build            # Build for production
npm run preview          # Preview production build

# Linting & Formatting
npm run lint            # Run ESLint
npm run format          # Format with Prettier

# Other
npm run start           # Alias for dev
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Navbar.jsx              # Navigation bar
│   │   ├── ProtectedRoute.jsx      # Auth guard
│   │   ├── FeatureCard.jsx         # Shared feature entry card
│   │   ├── PageHeader.jsx          # Shared page heading
│   │   └── layout/                 # Authenticated app shell
│   ├── pages/
│   │   ├── Landing.jsx             # Landing page
│   │   ├── Login.jsx               # Login page
│   │   ├── Signup.jsx              # Registration page
│   │   ├── Dashboard.jsx           # User dashboard
│   │   ├── InterviewSession.jsx    # Interview page
│   │   ├── InterviewHistory.jsx    # Searchable interview history
│   │   ├── AdaptiveInterview.jsx    # Adaptive interview flow
│   │   ├── CareerCoach.jsx          # Career analysis
│   │   └── Analytics.jsx           # Analytics page
│   ├── services/
│   │   └── api.js                  # API client
│   ├── contexts/
│   │   ├── AuthContext.jsx         # Auth state
│   │   └── InterviewContext.jsx    # Interview state
│   ├── hooks/
│   │   └── useHooks.js             # Custom hooks
│   ├── styles/
│   │   └── globals.css             # Global styles
│   ├── App.jsx                     # Main app
│   └── main.jsx                    # Entry point
├── public/                         # Static assets
├── index.html                      # HTML template
├── package.json
├── vite.config.js                  # Vite config
├── tailwind.config.js              # Tailwind config
├── postcss.config.js               # PostCSS config
├── Dockerfile
├── .env.example
└── README.md
```

## Environment Variables

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=InterviAI
VITE_APP_VERSION=1.0.0
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

## Pages

### Landing Page
- Hero section
- Feature showcase
- Call-to-action buttons

### Authentication Pages
- **Login**: Email/password authentication
- **Signup**: User registration
- Redirect to dashboard on success

### Dashboard
- Interview statistics
- Recent interview history
- Quick start interview buttons
- Performance overview

### Interview Session
- Question display
- Answer textarea
- AI evaluation on submit
- Progress tracking
- Skip question option

### Analytics
- Performance trends chart
- Category-wise performance
- Strengths and weaknesses
- Detailed metrics

## API Integration

API calls are centralized in `src/services/api.js`:

```javascript
// Authentication
authService.register(data)
authService.login(data)
authService.getProfile()

// Interview
interviewService.startInterview(data)
interviewService.generateQuestion(sessionId, category, difficulty)
interviewService.submitAnswer(data)
interviewService.endInterview(sessionId)

// Analytics
analyticsService.getDashboard()
analyticsService.getHistory(skip, limit)
analyticsService.getReport(sessionId)
analyticsService.getPerformanceTrend()
```

## State Management

### AuthContext
- User authentication state
- Login/logout functions
- Token management

### InterviewContext
- Current session data
- Current question data
- Submitted answers
- Interview flow management

## Authentication Flow

1. **Register/Login**: Submit credentials
2. **Token Storage**: Store JWT in localStorage
3. **Protected Routes**: Check auth before rendering
4. **API Requests**: Auto-include token in headers
5. **Token Refresh**: Auto-refresh expired tokens
6. **Logout**: Clear tokens and redirect

## Styling

### Tailwind CSS
- Dark theme by default
- Custom color variables
- Responsive breakpoints
- Utility-first approach

### Custom CSS
- Glassmorphism effect (`.glass`)
- Gradient text (`.gradient-text`)
- Smooth animations (`.fade-in`)
- Button variants (`.btn-primary`, `.btn-secondary`)

## Components

### Reusable Components
- `Navbar`: Navigation and user menu
- `ProtectedRoute`: Auth guard wrapper
- `Card`: Styled content container
- `Loading`: Loading spinner
- `Alert`: Error/success messages

### Page Components
- Landing, Login, Signup
- Dashboard, Interview, Analytics
- Profile, History, Reports

## Hooks

### Custom Hooks
- `useFetch`: Fetch with loading/error states
- `useLocalStorage`: Persist data to localStorage
- `useAuth`: Access auth context
- `useInterview`: Access interview context

## Performance Optimizations

- Code splitting with Vite
- Lazy loading pages with React.lazy
- Memoization with React.memo
- Asset compression
- CSS purging with Tailwind

## Development

### Debug Mode
Set `DEBUG=true` in .env

### Browser DevTools
- React DevTools extension
- Network tab for API debugging
- Console for errors

### CORS
- Backend CORS configured for frontend URL
- API requests proxied through Vite dev server

## Deployment

### Build for Production

```bash
npm run build
```

Creates optimized build in `dist/` folder.

### Deploy to Vercel

```bash
npm i -g vercel
vercel --prod
```

### Deploy to Other Platforms

See [DEPLOYMENT.md](/docs/DEPLOYMENT.md)

## Testing

```bash
# Unit tests (to be implemented)
npm run test

# E2E tests (to be implemented)
npm run test:e2e
```

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Common Issues

### API Connection Failed
- Check `VITE_API_URL` in .env
- Verify backend is running
- Check CORS settings

### Tokens Not Persisting
- Check localStorage is enabled
- Verify token format in browser storage
- Check token expiry

### UI Not Styling Correctly
- Run `npm install` to ensure Tailwind is installed
- Check tailwind.config.js
- Clear browser cache

## Performance

- **Bundle Size**: ~200KB (gzipped)
- **Load Time**: <2 seconds
- **Time to Interactive**: <3 seconds

## Accessibility

- Semantic HTML
- ARIA labels where needed
- Keyboard navigation support
- Color contrast compliance

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## Documentation

- [Architecture](../docs/ARCHITECTURE.md)
- [API Documentation](../docs/API_DOCUMENTATION.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)

## Support

- Issues: GitHub Issues
- Email: support@interviai.com
- Documentation: [https://github.com/yourusername/interviai](https://github.com/yourusername/interviai)

## License

MIT License - See LICENSE file

---

**Version**: 1.0.0  
**Last Updated**: January 2024
