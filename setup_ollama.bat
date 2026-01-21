@echo off
echo 🚀 Setting up Ollama for Jarvis Enterprise Assistant...

REM Check if Ollama is installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 Installing Ollama...
    winget install Ollama.Ollama
) else (
    echo ✅ Ollama already installed
)

echo 🚀 Starting Ollama server...
start /B ollama serve

timeout /t 5 /nobreak >nul

echo 📥 Downloading Mistral model...
ollama pull mistral

echo.
echo ✅ Setup complete!
echo 📡 Ollama server running on http://localhost:11434
echo 🤖 Model 'mistral' available
echo.
echo To test: ollama run mistral "Hello, I am Jarvis"
pause