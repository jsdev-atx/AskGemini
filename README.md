# Ask Gemini: Codebase Analyzer

This Python script uses Google's Gemini API to analyze a codebase and answer questions about it.  It's designed to handle multiple programming languages and provide a flexible way to interact with the LLM.

## Features

* **Multi-language Support:**  Analyzes code files with extensions `.php`, `.py`, `.js`, `.java`, `.cpp`, and `.h`.
* **Code Context:** Sends the entire codebase (or a specified portion) to the Gemini API as context for the question.
* **Flexible Question Input:** Accepts questions via command-line arguments or opens a system text editor for multiline questions.
* **Error Handling:** Includes robust error handling for API requests, file I/O, and encoding issues.
* **Environment Variable Configuration:** Uses environment variables for API keys, codebase paths, and excluded paths for security and flexibility.
* **Exclusion of Paths:** Allows specifying paths to exclude from analysis via the `EXCLUDED_PATHS` environment variable.


## Requirements

* Python 3.7+
* `google-generativeai`
* `python-dotenv`
* `requests` (optional, handled by google-generativeai)


Install required packages:

```bash
python3 -m pip install -r requirements.txt
```

## Setup

1. **Obtain a Gemini API Key:**  Get a Gemini API key from the Google AI Platform.
2. ** Set your Gemini API Key in your shell: ** 
   ```bash
    export GEMINI_API_KEY="your-key-here"
    source ~/.bashrc
    echo $GEMINI_API_KEY
   ```
**Note: ** If using MacOS, you're likely using `zsh`. Just change the `source ~/.bashrc` to `source ~/.zshrc`.
   
3. **Set Environment Variables:** Create a `.env` file (or set the variables directly in your shell) with the following:

   ```
   CODEBASE_PATH=/path/to/your/codebase  # Optional, defaults to the current directory.
   EXCLUDED_PATHS=path/to/exclude1,path/to/exclude2  # Optional, comma-separated list of paths to exclude.
   ```

4. **(Optional) Set EDITOR environment variable:** If you want to use a specific text editor for multiline question input, set the `EDITOR` environment variable (e.g., `export EDITOR=vim` or `export EDITOR=nano`).  If unset, the script defaults to `vi`.


## Usage

**Command-line arguments:**

* `-q`, `--question`: Provide your question as a command-line argument.
* `-e`, `--editor`: Open a text editor to write a multiline question.  Only use this *or* `-q`, not both.

**Examples:**

* **Single-line question:**

```bash
python ask_gemini.py -q "What is the purpose of function 'calculate_total'?"
```

* **Multiline question (using editor):**

```bash
python ask_gemini.py -e
```

This will open your default text editor, allowing you to input a more complex question.


## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

GNU General Public License v3.0
```
