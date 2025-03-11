# Network Troubleshooting Assistant

A Flask-based web application that provides an interactive network troubleshooting assistant, powered by Ollama for LLM capabilities and ChromaDB for document retrieval.

## Features

- Interactive chat interface for network troubleshooting
- Intelligent problem type detection
- Guided information gathering system
- Document indexing for knowledge retrieval
- Context-aware responses leveraging your network documentation
- Environment-based configuration system

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Ollama running locally or on a remote server
- Network documentation (optional, but recommended)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd network-troubleshooting-assistant
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file by copying the sample:
   ```bash
   cp .env.sample .env
   ```

5. Edit the `.env` file to match your environment:
   ```
   # Primary configuration
   OLLAMA_HOST=http://your-ollama-server:11434
   OLLAMA_MODEL=network-assistant
   ```

6. Start the application:
   ```bash
   python app.py
   ```

7. Open a web browser and go to `http://localhost:5000`

## Configuration

The application uses environment variables for configuration, which can be set in a `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DOCS_DIR` | Directory for storing network documentation | `./network_docs` |
| `DB_DIR` | Directory for ChromaDB storage | `./chroma_db` |
| `CHUNK_SIZE` | Size of text chunks for indexing | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `SEARCH_RESULTS` | Number of search results to retrieve | `5` |
| `OLLAMA_HOST` | URL of your Ollama instance | `http://localhost:11434` |
| `OLLAMA_MODEL` | Name of the Ollama model to use | `network-assistant` |
| `PORT` | Port to run the application on | `5000` |
| `DEBUG_MODE` | Enable Flask debug mode | `False` |

## Document Indexing

For best results, place your network documentation in the `network_docs` directory (or your custom configured directory). Supported formats:

- Markdown (`.md`)
- Text files (`.txt`)
- YAML configuration files (`.yaml`, `.yml`)

After adding documents, click the "Index Documents" button in the UI to make them searchable.

## Troubleshooting

### ChromaDB Issues

If you see "ChromaDB not available" messages:
- Make sure you've installed the required packages
- Check if there are compatibility issues with your Python version
- Consider manually installing ChromaDB: `pip install chromadb`

### Ollama Connection Issues

If you see "Could not connect to Ollama":
- Verify that Ollama is running
- Check that the `OLLAMA_HOST` setting points to the correct URL
- Make sure your network allows connections to the Ollama server
- Verify that the model specified in `OLLAMA_MODEL` is available on your Ollama instance

## Security Notes

- This application is designed for internal network use only
- There is no authentication built into the application
- Do not expose this service to the public internet without adding proper security measures

## License

[MIT License]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.