# Siraj – Local-First Study Companion

<p align="center">
  <img src="media/logo.png" alt="Siraj Logo" width="200"/>
</p>

<p align="center">
  <em>An AI-powered learning companion that transforms your documents into interactive study experiences</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## 🌟 Overview

Siraj is a **local-first, AI-powered study companion** that helps you master any subject by transforming your documents into interactive learning experiences. Upload PDFs, generate summaries, create quizzes, chat with your documents, and track your progress—all while keeping your data private and local.

### Key Benefits
- **🔒 Privacy-First**: All data stays on your machine
- **🤖 AI-Powered**: Leverages local LLMs for intelligent content processing
- **📚 Multi-Modal**: Text summaries, video recaps, and interactive quizzes
- **📊 Progress Tracking**: Detailed analytics and learning insights
- **🎯 Personalized**: Adaptive recommendations based on your performance

## ✨ Features

### 📖 Document Processing
- **Multi-format support**: PDFs, text files, and more
- **OCR capabilities**: Extract text from scanned documents
- **Smart chunking**: Intelligent document segmentation for better AI processing

### 🧠 AI-Powered Learning
- **Intelligent Summaries**: Auto-generated summaries with key insights
- **Interactive Q&A**: Chat with your documents using RAG (Retrieval-Augmented Generation)
- **Quiz Generation**: Automatically create multiple-choice questions with explanations
- **Brainrot Videos**: Generate engaging TTS-powered video summaries with captions

### 📊 Progress Tracking
- **Learning Analytics**: Track completion rates, streaks, and skill mastery
- **Performance Insights**: Identify weak areas and get targeted recommendations
- **Visual Dashboard**: Beautiful charts and progress visualization

### 🎯 Smart Features
- **Sentiment Analysis**: Track learning mood and engagement
- **Targeted Reviews**: Focus on topics that need improvement
- **Weekly Planning**: AI-curated study plans and resource recommendations

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Ollama** (for local LLM)
- **FFmpeg** (for video processing)

### 1. Clone the Repository
```bash
git clone https://github.com/amine-maazizi/Siraj.git
cd Siraj
```

### 2. Install Ollama and Pull Models
```bash
# Install Ollama (visit https://ollama.ai for your platform)
# Then pull the required models:
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 3. Set Up Python Backend
```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Up Node.js Frontend
```bash
cd app
npm install
cd ..
```

### 5. Configure Environment
```bash
# Set Ollama URL (adjust if needed)
# Windows PowerShell
$env:OLLAMA_BASE_URL="http://localhost:11434"

# macOS/Linux
export OLLAMA_BASE_URL="http://localhost:11434"
```

### 6. Run the Application
```bash
# Terminal 1: Start the backend server
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend
cd app
npm run dev
```

### 7. Access Siraj
Open your browser and navigate to `http://localhost:3000`

## 📋 Installation

### System Dependencies

#### Windows
```powershell
# Install FFmpeg
winget install Gyan.FFmpeg

# Install espeak (for TTS alignment)
# Download from: http://espeak.sourceforge.net/download.html
```

#### macOS
```bash
# Install using Homebrew
brew install ffmpeg espeak sox
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg espeak espeak-data libespeak1 libespeak-dev sox
```

### Python Environment Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. **Install Node.js Dependencies**:
   ```bash
   cd app
   npm install
   ```

2. **Build for Production** (optional):
   ```bash
   npm run build
   npm start
   ```

## 🎯 Usage

### Creating Your First Project

1. **Start the Application**: Follow the Quick Start guide above
2. **Create a New Project**: Click "New Project" and enter your subject and learning goals
3. **Upload Documents**: Drag and drop PDFs or text files to get started
4. **Explore Features**:
   - **Summary**: Generate AI-powered summaries of your content
   - **Chat**: Ask questions about your documents
   - **Quiz**: Test your knowledge with auto-generated questions
   - **Review**: Get targeted recommendations for improvement
   - **Dashboard**: Track your learning progress

### Advanced Configuration

#### Environment Variables

Create a `.env` file in the root directory:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text

# Project Configuration
SIRAJ_PROJECTS_DIR=./SirajProjects
SIRAJ_DEFAULT_PROJECT=ExampleProject

# Summarization Settings
SUMMARIZE_TOPK=200
SUMMARIZE_MAX_MAP_CHUNKS=60
```

#### Custom Models

You can use different Ollama models by updating the environment variables:

```bash
# Pull alternative models
ollama pull mistral
ollama pull codellama

# Update environment
export OLLAMA_LLM_MODEL=mistral
```

## 🏗 Tech Stack

### Frontend
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **UI Components**: Custom components with shadcn/ui patterns
- **State Management**: Zustand + TanStack Query
- **Forms**: React Hook Form + Zod validation
- **PDF Viewer**: PDF.js
- **Charts**: Recharts
- **Animations**: Framer Motion

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **AI/ML**: LangChain + Ollama
- **Vector Database**: ChromaDB
- **Document Processing**: PyPDF, Unstructured, Tesseract OCR
- **TTS/Video**: Coqui TTS, FFmpeg, MoviePy
- **Validation**: Pydantic + Instructor

### Storage
- **Project Data**: SQLite (`.sirajproj` files)
- **Vector Embeddings**: ChromaDB
- **Media Files**: Local file system

### AI Models
- **LLM**: Llama 3.1 8B Instruct (via Ollama)
- **Embeddings**: nomic-embed-text
- **TTS**: Coqui XTTS v2
- **Sentiment**: VADER + Transformers

## 📁 Project Structure

```
Siraj/
├── app/                    # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   ├── lib/          # Utilities and configs
│   │   └── types/        # TypeScript definitions
│   └── public/           # Static assets
├── server/                # FastAPI backend
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── utils/           # Helper functions
│   └── store/           # Local data storage
├── SirajProjects/        # User projects
├── shared/              # Shared schemas
└── tests/              # Test suites
```

## 🧪 Development

### Running Tests
```bash
# Python tests
pytest tests/

# Frontend tests (if configured)
cd app
npm test
```

### Code Quality
```bash
# Python formatting
black server/
isort server/

# Frontend linting
cd app
npm run lint
```

### Database Management
```bash
# Clear all data (be careful!)
python clear_data.py

# Or use the batch file on Windows
clear_data.bat
```

## 🔧 Troubleshooting

### Common Issues

#### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Check connection
curl http://localhost:11434/api/tags
```

#### Python Environment Issues
```bash
# Verify Python version
python --version

# Check virtual environment
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Frontend Build Issues
```bash
# Clear Node modules and reinstall
cd app
rm -rf node_modules package-lock.json
npm install

# Clear Next.js cache
npm run build -- --no-cache
```

### Performance Tips
- **Memory**: Ensure at least 8GB RAM for optimal LLM performance
- **Storage**: Keep at least 10GB free space for models and projects
- **GPU**: NVIDIA GPU support available with CUDA-enabled Ollama

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Standards
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow project ESLint configuration
- **Commits**: Use conventional commit messages
- **Testing**: Add tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama Team** for making local LLMs accessible
- **LangChain** for the excellent AI framework
- **Next.js Team** for the amazing React framework
- **FastAPI** for the high-performance Python web framework
- **ChromaDB** for the vector database solution

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/amine-maazizi/Siraj/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amine-maazizi/Siraj/discussions)
- **Documentation**: [Project Wiki](https://github.com/amine-maazizi/Siraj/wiki)

## 🗺️ Roadmap

- [ ] **Mobile App**: React Native companion app
- [ ] **Cloud Sync**: Optional cloud backup and sync
- [ ] **Collaborative Features**: Share projects and study together
- [ ] **Advanced Analytics**: Machine learning insights
- [ ] **Plugin System**: Extensible architecture for custom features
- [ ] **Multi-language Support**: Internationalization

---

<p align="center">
  Made with ❤️ by the Siraj Team
</p>
