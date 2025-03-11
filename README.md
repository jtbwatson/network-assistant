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

### Model Setup with Ollama

To create the custom network troubleshooting model:

1. Install Ollama from the official website (https://ollama.com/)

2. Create a Modelfile for the network assistant:
   ```bash
   nano network-assistant.modelfile
   ```

3. Copy the following content into the Modelfile:
   ```dockerfile
   FROM llama3.2

   # Metadata about the model
   PARAMETER temperature 0.7
   PARAMETER top_p 0.9
   PARAMETER stop "<|im_end|>"

   # System prompt that defines the assistant's behavior
   SYSTEM """
   You are a Network Troubleshooting Assistant, an expert system designed to help IT professionals diagnose and resolve networking issues. Your knowledge covers:

   1. Network protocols (TCP/IP, DNS, DHCP, HTTP/S, SSH, FTP, etc.)
   2. Network infrastructure (routers, switches, firewalls, load balancers)
   3. Network services and applications
   4. Connectivity issues and their resolution
   5. Performance optimization
   6. Security best practices
   7. Wireless networking
   8. VPNs and remote access
   9. Cloud networking concepts
   10. Network monitoring and diagnostics

   When helping users:
   - Ask clarifying questions to properly diagnose issues
   - Provide step-by-step troubleshooting procedures
   - Explain concepts clearly using technical terms appropriately
   - Offer both immediate fixes and long-term solutions when relevant
   - Respect network security best practices
   - Reference specific commands, tools, or configurations when appropriate
   - Admit when you need more information to provide an accurate solution

   You should adapt your responses based on the technical level of the user. For basic questions, provide educational explanations. For advanced issues, focus on efficient technical solutions.
   """
   ```

4. Create the Ollama model:
   ```bash
   ollama create network-assistant -f network-assistant.modelfile
   ```

5. Verify the model is created:
   ```bash
   ollama list
   ```

You should see `network-assistant` in the list of available models.

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
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=network-assistant
   ```

6. Start the application:
   ```bash
   python app.py
   ```

7. Open a web browser and go to `http://localhost:5000`

## Model Details

### Base Model
- The assistant uses Llama 3.2 as its foundational language model
- Specialized with a custom system prompt for network troubleshooting

### Model Configuration
- **Temperature**: 0.7 (balanced between creativity and determinism)
- **Top P**: 0.9 (allows diverse but relevant responses)
- **Stopping Criteria**: Configured to stop at `<|im_end|>`

### Capabilities
The model is specifically trained to:
- Diagnose network issues
- Provide technical guidance
- Explain networking concepts
- Offer troubleshooting steps
- Adapt to different technical skill levels

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