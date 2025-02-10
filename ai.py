import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# google/flan-t5-large, google/flan-t5-base, google/flan-t5-small, "gpt2"
MODEL_NAME = "google/flan-t5-base"
MODEL_NAME_2 = "gpt2"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

generator = pipeline("text-generation", model=MODEL_NAME_2)


def cover_letter_generator_one(
    job_title, company_name, job_description, skills, experience, max_length=500
):
    """
    Generates a professional cover letter using a free text-generation model.

    Parameters:
        job_title (str): The job title for which the cover letter is being written.
        company_name (str): The company name.
        job_description (str): A description of the job.
        applicant_skills_experience (str): The applicant's skills and experience.
        max_length (int): Maximum token length for generated text.

    Returns:
        str: A generated cover letter text.
    """
    # Create a prompt that instructs the model to generate a tailored cover letter.
    prompt = (
        f"Write a professional cover letter as an applicant applying for the position of {job_title} at {company_name} company.\n"
        f"Job Description: {job_description}\n"
        f"Applicant Skills: {skills}\n"
        f"Applicant Experience: {experience}\n"
        "The cover letter should be engaging, professional, and tailored to the job description. "
        "Keep it under 500 words.\n\n"
    )

    # Generate the cover letter text.
    generated = generator(
        prompt, truncation=True, max_new_tokens=max_length, num_return_sequences=1
    )
    # The generated text includes the prompt; you might want to process it further.
    cover_letter = generated[0]["generated_text"]
    return cover_letter


def truncate_text(text: str, max_tokens: int = 300) -> str:
    tokens = tokenizer.encode(text, max_length=max_tokens, truncation=True)
    return tokenizer.decode(tokens, skip_special_tokens=True)


def cover_letter_generator(
    job_title: str,
    company_name: str,
    job_description: str,
    skills: str,
    experience: str,
) -> str:
    try:
        # Truncate long inputs
        job_description = truncate_text(job_description)
        experience = truncate_text(experience)

        # Structured prompt
        prompt = f"""
        Task: Generate a formal cover letter for a job application.
        Job Title: {job_title}
        Company: {company_name}
        Job Description: {job_description}
        Applicant Skills: {skills}
        Applicant Experience: {experience}
        Instructions:
        1. Address the hiring manager.
        2. Highlight 2-3 skills from "Applicant Skills".
        3. Mention experience from "Applicant Experience".
        4. Keep it under 300 words.
        Output:
        """
        logger.info("Prompt: %s", prompt)  # Debug prompt

        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(
            inputs.input_ids,
            max_new_tokens=500,
            temperature=0.9,
            do_sample=True,
            top_k=50,
            top_p=0.95,
        )
        letter = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove redundant instructions (if any)
        letter = letter.split("Output:")[-1].strip()
        return letter
    except (ValueError, RuntimeError, torch.TorchError) as e:
        logger.error("Error: %s", e)
        return "Failed to generate letter. Please try again."
