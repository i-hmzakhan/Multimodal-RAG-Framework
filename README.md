Multimodal-RAG-Framework
A modular, vision-enabled Retrieval-Augmented Generation (RAG) engine designed for complex academic document retrieval. This framework bridges the gap between static lecture materials and interactive AI by utilizing Computer Vision to interpret diagrams, slides, and handwritten notes.

🧠 Core Architecture
The framework is divided into specialized modules to ensure scalability:

Vision Module: Leverages Tesseract-OCR to extract text from images and diagrams within lecture slides.

RAG Engine: Utilizes ChromaDB for vector storage and Sentence-Transformers for high-dimensional text embeddings.

Context Manager: Handles the retrieval and synthesis of information using Google Gemini.

🎓 Implementation: AI Study Assistant
The primary implementation of this framework is a desktop-based AI Study Assistant.

Lecture Parsing: Automatically processes PDFs, PowerPoints, and YouTube transcripts.

Multimodal Retrieval: Identifies diagrams within notes and provides a "View Diagram" feature directly in the chat.

Modern UI: Built with CustomTkinter for a sleek, dark-themed user experience.

🛠️ Setup & Installation
1. Prerequisites
Python 3.11.9

Tesseract-OCR: Must be installed or bundled in the Tessereact/ folder.

2. Environment Configuration
Create a .env file in the root directory and add your API keys:

Code snippet
GEMINI_API_KEY=your_key_here
3. Installation
Activate your virtual environment and install dependencies:

PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
📁 Repository Structure
Plaintext
Multimodal-RAG-Framework/
├── src/
│   ├── core/           # RAG Engine & Vector DB logic
│   ├── vision/         # OCR & Image Processing
│   └── apps/
│       └── assistant/  # GUI implementation
├── requirements.txt    # Project dependencies
└── README.md

✨ Key Qualities & Features
🛠️ Technical Robustness
Multimodal Intelligence: Unlike standard RAG systems, this engine extracts and indexes text from complex diagrams and lecture slides using OCR.

Persistent Vector Memory: Utilizes ChromaDB to ensure your processed lectures remain available across sessions without re-processing.

Intelligent Chunking: Implements context-aware splitting for PDFs, PPTX, and YouTube transcripts to maintain semantic meaning.

🎨 User-Centric Design
Modern Aesthetic: A fully customized Dark Mode interface built with CustomTkinter for comfortable long-term study sessions.

Real-time Feedback: Includes a progress tracking system that gives visual feedback during the document embedding process.

Interactive Citations: Every AI response includes clickable sources. If the AI references a diagram, a "View Diagram" button appears to show the exact visual context.

🚀 Portability & Deployment
Standalone Executable: The implementation is "frozen" into a portable .exe that bundles its own Python environment and OCR engine.

Zero-Install OCR: Features a bundled Tessereact environment, allowing the app to run on machines without pre-installed OCR software.
The .exe file is bigger than github allows to upload. However, the owner can share it through google drive upon request.

   Bazeeche e Atfaal hain Dunya Mere Aagay,
   Hota hain Shab o Roz Tamasha Mere Aagay!
