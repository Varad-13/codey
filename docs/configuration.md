# Configuration

Before using Codey, it's essential to set up your environment correctly. The following instructions will guide you through the configuration process.

## Required Environment Variables
To function properly, Codey requires certain environment variables to be set:

- **OPENAI_API_KEY**: This is required for accessing AI functionalities. You can obtain an API key by signing up at OpenAI's website.
- **OPENAI_BASE_URL** (optional): Specify a custom OpenAI-compatible API base URL. If not set, Codey will use the default OpenAI API endpoint.
- **MODEL_NAME** (optional): Specify the AI model you wish to use. If not set, Codey will default to a specified model.

## Setting Up Environment Variables
To set environment variables, you can do so directly in your terminal or use a `.env` file for convenience.

### Using Terminal
For Unix-based systems (Linux, macOS), you can export the variables as follows:
```bash
export OPENAI_API_KEY='your_api_key'
export OPENAI_BASE_URL='https://your-custom-openai-server.com/v1'  # Optional
export MODEL_NAME='your_model_name'
```

For Windows:
```cmd
set OPENAI_API_KEY='your_api_key'
set OPENAI_BASE_URL='https://your-custom-openai-server.com/v1'  # Optional
set MODEL_NAME='your_model_name'
```

### Using a .env File
You can also create a `.env` file in your project root with the following format:
```
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://your-custom-openai-server.com/v1  # Optional
MODEL_NAME=your_model_name
```

## Validate Configuration
To confirm that your environment variables are set correctly, you can run:
```bash
echo $OPENAI_API_KEY
```
This should output your API key. If you see an empty response, please ensure you've set the variable correctly.