# UniCounsel - University Counseling Platform

UniCounsel एक comprehensive platform है जो students को अपने profile के based पर best universities find करने में help करता है।

## Features

- **University Matching**: Student profile के based पर personalized university recommendations
- **Global Database**: 9000+ universities worldwide
- **Advanced Search**: Country, city, और field based filtering
- **Cost Calculator**: Tuition और living costs का estimation
- **Match Scoring**: Academic, financial, language, और visa fit analysis
- **Map Explorer**: Interactive map पर universities देखें
- **Document Generator**: Application documents generate करें
- **Scholarship Finder**: Available scholarships search करें

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- React Router
- Leaflet (Maps)

### Backend
- Node.js + Express
- TypeScript
- JSON-based data storage

## Setup Instructions

### Prerequisites
- Node.js 18+ 
- npm या yarn

### 1. Clone Repository

```bash
git clone <repository-url>
cd unicounsel
```

### 2. Install Dependencies

**Frontend:**
```bash
npm install
```

**Backend:**
```bash
cd backend
npm install
cd ..
```

### 3. Convert CSV to JSON

Backend में universities data use करने के लिए CSV को JSON में convert करें:

```bash
npm run convert:csv
```

या manually:

```bash
cd backend
npx tsx scripts/convertCsvToJson.mts
```

यह `public/unidata.csv` को read करके `backend/data/universities.json` में convert करेगा।

### 4. Start Development Servers

**Option 1: Separate Terminals**

Terminal 1 - Frontend:
```bash
npm run dev
```

Terminal 2 - Backend:
```bash
npm run dev:backend
```

**Option 2: Single Command (if concurrently installed)**
```bash
npm run dev:all
```

### 5. Access Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:4000
- API Health Check: http://localhost:4000/api/health

## Project Structure

```
unicounsel/
├── backend/                 # Backend API server
│   ├── data/               # JSON data files
│   ├── scripts/            # Utility scripts
│   ├── controllers/        # Request handlers
│   ├── services/           # Business logic
│   ├── routes/             # API routes
│   ├── middleware/         # Express middleware
│   ├── types/              # TypeScript types
│   └── server.mts          # Main server file
├── src/                    # Frontend source code
│   ├── components/         # React components
│   ├── pages/              # Page components
│   ├── services/           # API services
│   ├── config/             # Configuration files
│   ├── context/            # React contexts
│   ├── hooks/              # Custom hooks
│   ├── lib/                # Utility functions
│   └── types/              # TypeScript types
├── public/                 # Static assets
│   └── unidata.csv         # Original CSV data
└── package.json
```

## API Endpoints

### Universities
- `GET /api/universities` - Get all universities
- `GET /api/universities/search` - Search universities
- `GET /api/universities/:id` - Get university by ID
- `GET /api/universities/countries` - Get all countries
- `GET /api/universities/countries/:country` - Get universities by country
- `GET /api/universities/countries/:country/cities` - Get cities by country
- `GET /api/universities/stats` - Get statistics

### Matching
- `POST /api/matches` - Find best matches
- `POST /api/matches/country/:country` - Find matches by country

Detailed API documentation: [backend/README.md](backend/README.md)

## Environment Variables

### Frontend
Create `.env` file in root:
```env
VITE_API_BASE_URL=http://localhost:4000/api
```

### Backend
Create `backend/.env` file:
```env
PORT=4000
NODE_ENV=development
```

## Build for Production

### Frontend
```bash
npm run build
```

### Backend
```bash
cd backend
npm start
```

## Data Source

Universities data `public/unidata.csv` file से आता है जिसमें 9000+ universities की information है:
- University name
- URL
- Location (latitude, longitude)
- Address
- Country और City

यह data automatically JSON format में convert होता है backend में use करने के लिए।

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

Issues या questions के लिए GitHub issues create करें।

