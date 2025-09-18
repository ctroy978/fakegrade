# AI Grader

This command-line application uses the Google Gemini API to evaluate a student paper against a provided rubric.

## Setup and Installation

### 1. Prerequisites

- Python 3.10 or higher.

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

- **On macOS and Linux:**

  ```bash
  source venv/bin/activate
  ```

- **On Windows:**

  ```bash
  .\venv\Scripts\activate
  ```

### 4. Install Dependencies

Install the required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Set Up the Google Gemini API Key

This project requires a Google Gemini API key. You can obtain one from the [Google AI Studio](https://aistudio.google.com/app/apikey).

For security, the API key is loaded from an environment variable. You can set this up in one of two ways:

- **Create a `.env` file:**

  Create a file named `.env` in the project root and add your API key:

  ```
  GEMINI_API_KEY="YOUR_API_KEY"
  ```

- **Set an environment variable directly:**

  - **On macOS and Linux:**

    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
    ```

  - **On Windows (Command Prompt):**

    ```bash
    set GEMINI_API_KEY="YOUR_API_KEY"
    ```

  - **On Windows (PowerShell):**

    ```powershell
    $env:GEMINI_API_KEY="YOUR_API_KEY"
    ```

## Usage

Run the `evaluate.py` script from your terminal, providing the paths to the rubric PDF and the student paper PDF as arguments.

```bash
python evaluate.py <path_to_rubric.pdf> <path_to_student_paper.pdf>
```

**Example:**

```bash
python evaluate.py rubric.pdf student_paper.pdf
```

## Example Output

The script will output the evaluation results to the console. The format will be determined by the Gemini API's response to the prompt.

```
--- Evaluation Results ---

**Overall Summary:**

The student paper provides a solid overview of the topic, demonstrating a good understanding of the key concepts. The arguments are generally well-supported, but some sections could benefit from more detailed evidence.

**Rubric Criteria:**

*   **Clarity (Score: 4/5):** The paper is well-written and easy to follow.
*   **Argumentation (Score: 3/5):** The arguments are logical, but some claims lack sufficient evidence.
*   **Use of Sources (Score: 4/5):** The paper effectively uses a variety of sources to support its claims.

--- End of Evaluation ---
```

## Error Handling

The script includes error handling for common issues such as:

-   File not found
-   Invalid PDF files
-   Missing API key
-   API errors

If an error occurs, a descriptive message will be printed to the standard error stream.
