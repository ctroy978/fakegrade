
import os
import sys
import argparse
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv

def setup_api_key():
    """
    Loads the Gemini API key from environment variables.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{pdf_path}' was not found.")
    except Exception as e:
        raise IOError(f"Error reading PDF file '{pdf_path}': {e}")

def evaluate_paper(rubric_text, paper_text):
    """
    Evaluates the student paper against the rubric using the Gemini API.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Evaluate this student paper based on the following rubric.
        Provide a score for each rubric criterion and an overall summary.

        Rubric:
        {rubric_text}

        Student Paper:
        {paper_text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Error during Gemini API call: {e}")

def main():
    """
    Main function to run the evaluation script.
    """
    parser = argparse.ArgumentParser(description="Evaluate a student paper against a rubric.")
    parser.add_argument("rubric_pdf", help="The path to the rubric PDF file.")
    parser.add_argument("student_paper_pdf", help="The path to the student paper PDF file.")
    args = parser.parse_args()

    try:
        setup_api_key()
        rubric_text = extract_text_from_pdf(args.rubric_pdf)
        paper_text = extract_text_from_pdf(args.student_paper_pdf)
        evaluation = evaluate_paper(rubric_text, paper_text)

        print("\n--- Evaluation Results ---")
        print(evaluation)
        print("--- End of Evaluation ---\n")

    except (ValueError, FileNotFoundError, IOError, RuntimeError) as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
