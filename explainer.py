# STEP 1: EXPLAINER.PY
# Read the configuration and build a Gemini explanation chain.


# ---------------------------------------------------------
# PART 1: IMPORT THE REQUIRED LIBRARIES
# ---------------------------------------------------------

import os  # Read API keys and model names from system environment variables.

from pathlib import Path  # Handle file and folder paths.

from dotenv import dotenv_values  # Read configuration file settings into a dictionary-like object.

from langchain_google_genai import ChatGoogleGenerativeAI  # Use Gemini chat models through LangChain.

from langchain_core.prompts import ChatPromptTemplate  # Build a prompt containing instructions, examples, and user input.

from langchain_core.output_parsers import StrOutputParser  # Extract plain text from the model's response.


# ---------------------------------------------------------
# PART 2: LOCATE YOUR CONFIGURATION FILE
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent  # Get the absolute path of the folder containing explainer.py.

ENV_PATH = BASE_DIR / ".env.example"  # Build the full path to .env.example in the same folder.


# ---------------------------------------------------------
# PART 3: DEFINE A CONFIGURATION ERROR
# ---------------------------------------------------------

class ConfigurationError(Exception):  # Create a custom exception for configuration problems.
    """Report missing or incomplete application settings."""  # Describe the purpose of this exception.

    pass  # Use the inherited Exception behaviour without adding custom behaviour.


# ---------------------------------------------------------
# PART 4: READ AND VALIDATE THE CONFIGURATION
# ---------------------------------------------------------

def read_configuration():  # Define a function that reads and validates the API key and model name.

    file_settings = (  # Store the settings read from the configuration file.
        dotenv_values(ENV_PATH)  # Read the configuration file into a dictionary-like object.
        if ENV_PATH.is_file()  # Read it only if a file exists at the specified path.
        else {}  # Use an empty dictionary if the file does not exist.
    )  # Complete the conditional expression.

    api_key = (  # Select an API key from the available sources.
        file_settings.get("GOOGLE_API_KEY")  # First, try the API key in the configuration file.
        or os.getenv("GOOGLE_API_KEY")  # If the file value is missing or empty, check the environment variable.
        or ""  # Use an empty string if neither source provides a key.
    ).strip()  # Remove leading and trailing whitespace from the selected value.

    if not api_key and not ENV_PATH.is_file():  # Check whether both the API key and configuration file are missing.
        raise ConfigurationError(  # Raise an error and stop normal execution.
            f"Cannot find the configuration file at: {ENV_PATH}\n\n"  # Include the expected file path in the message.
            "Create .env.example beside app.py and add GOOGLE_API_KEY."  # Explain how to provide the missing configuration.
        )  # Complete the error message.

    placeholders = {  # Define example key values that must be replaced with a real API key.
        "replace_with_your_actual_api_key",  # First possible placeholder value.
        "your_actual_gemini_api_key",  # Second possible placeholder value.
        "your_actual_api_key",  # Third possible placeholder value.
    }  # Complete the set of placeholder values.

    if not api_key or api_key in placeholders:  # Reject an empty key or a key matching a listed placeholder.
        raise ConfigurationError(  # Raise an error for the invalid configuration.
            "GOOGLE_API_KEY is empty or contains a placeholder. "  # Explain the configuration problem.
            "Enter your actual API key in .env.example and save the file."  # Explain how to correct the problem.
        )  # Complete the error message.

    model_name = (  # Select a Gemini model name from the available sources.
        file_settings.get("GEMINI_MODEL")  # First, try the model name in the configuration file.
        or os.getenv("GEMINI_MODEL")  # If the file value is missing or empty, check the environment variable.
        or "gemini-3.8-flash"  # Use this default string if needed; this does not verify model availability.
    ).strip()  # Remove leading and trailing whitespace from the selected model name.

    if not model_name:  # Check whether the model name is empty after removing whitespace.
        raise ConfigurationError(  # Raise an error for the empty model name.
            "GEMINI_MODEL is empty. "  # Explain why the configuration is invalid.
            "Add a valid model name to .env.example."  # Explain how to correct the model setting.
        )  # Complete the error message.

    return api_key, model_name  # Return both settings as a tuple without printing the API key.


# ---------------------------------------------------------
# PART 5: BUILD THE EXPLANATION CHAIN
# ---------------------------------------------------------

def build_chain():  # Define a function that prepares the prompt, model, and output parser.

    api_key, model_name = read_configuration()  # Read the configuration and unpack the two returned values.

    llm = ChatGoogleGenerativeAI(  # Create a configured Gemini model object; no question is sent here.
        model=model_name,  # Select the model specified in the configuration.
        api_key=api_key,  # Provide the API key for authentication.
        vertexai=False,  # Configure the integration to use the Gemini Developer API.
        temperature=1.0,  # Configure randomness in response sampling.
        max_tokens=4096,  # Configure the maximum generated token budget.
        timeout=60,  # Configure the API request timeout in seconds.
        max_retries=2,  # Allow up to two retries for eligible temporary failures.
    )  # Complete the model configuration.

    system_instructions = (  # Define the AI teacher's behaviour and expected answer structure.
        "You are a patient AI teacher who explains concepts clearly.\n"  # Assign the role of a patient teacher.
        "Adapt the explanation to the student's learning level.\n"  # Adjust the explanation to the selected learning level.
        "Write the explanation in {language}.\n"  # Use the language supplied when the chain runs.
        "For Hinglish, use simple Hindi and English in Roman script.\n"  # Write Hinglish using English letters.
        "Use simple language and explain necessary technical terms.\n"  # Keep the explanation accessible and define technical terms.
        "Include four sections: Meaning, How it works, Example, "  # Specify the first three required sections.
        "and Key takeaway.\n"  # Specify the fourth section; this string joins the previous string.
        "Translate section headings when appropriate for the language.\n"  # Allow headings to match the selected language.
        "Include a practical example and an analogy when helpful.\n"  # Request practical examples and useful comparisons.
        "The examples demonstrate structure, not the required language.\n"  # Use examples for structure while following the requested language.
        "Aim for approximately 250 to 400 words.\n"  # Request an approximate answer length.
        "If the topic is ambiguous, ask a short clarification question.\n"  # Ask for clarification when the topic is unclear.
        "If uncertain about a fact, acknowledge the uncertainty."  # State uncertainty instead of presenting an uncertain fact confidently.
    )  # Combine the adjacent strings into one instruction string.

    example_1_question = (  # Define the first sample user question.
        "Topic: Supervised Learning\n"  # Set supervised learning as the sample topic.
        "Learning level: Beginner"  # Set beginner as the sample learning level.
    )  # Complete the first sample question.

    example_1_answer = (  # Define an example answer demonstrating the desired structure.
        "Meaning: Supervised learning trains a model using examples "  # Introduce supervised learning in the Meaning section.
        "with known answers, called labels.\n\n"  # Explain labels and add a blank line before the next section.

        "How it works: The model makes predictions, compares them "  # Introduce the prediction step.
        "with the labels, and adjusts to reduce errors. "  # Explain comparison with labels and error reduction.
        "We then evaluate it on unseen data.\n\n"  # Explain that evaluation uses unseen data.

        "Example: A spam classifier learns from emails labelled "  # Introduce a practical spam classification example.
        "spam or not spam. This resembles practising with "  # Describe the labels and begin an analogy.
        "questions that have an answer key.\n\n"  # Complete the analogy using practice questions with known answers.

        "Key takeaway: Labelled examples help a model learn "  # Introduce the main lesson.
        "to predict answers for new inputs."  # Explain the goal of predicting answers for new inputs.
    )  # Complete the first sample answer.

    example_2_question = (  # Define the second sample user question.
        "Topic: Overfitting\n"  # Set overfitting as the sample topic.
        "Learning level: Beginner"  # Set beginner as the sample learning level.
    )  # Complete the second sample question.

    example_2_answer = (  # Define another example answer using the same structure.
        "Meaning: Overfitting occurs when a model learns training "  # Introduce overfitting in the Meaning section.
        "details and noise that do not generalise well to new data.\n\n"  # Explain why learning noise harms generalisation.

        "How it works: Training performance is strong, but "  # Describe strong performance on training data.
        "performance on unseen examples is worse.\n\n"  # Contrast this with weaker performance on unseen data.

        "Example: A student memorises practice answers but "  # Begin an analogy about memorising answers.
        "struggles when exam questions change.\n\n"  # Explain the difficulty of handling unfamiliar questions.

        "Key takeaway: Evaluate models on unseen data, "  # State the importance of evaluation on unseen data.
        "rather than judging them only on training results."  # Explain why training results alone are insufficient.
    )  # Complete the second sample answer.

    student_request = (  # Define a reusable template for the actual student's request.
        "Explain the following topic:\n"  # Ask the model to explain the supplied topic.
        "Topic: {topic}\n"  # Insert the actual topic when the chain runs.
        "Learning level: {level}\n"  # Insert the selected learning level when the chain runs.
        "Language: {language}"  # Insert the selected response language when the chain runs.
    )  # Complete the student request template.

    prompt = ChatPromptTemplate.from_messages([  # Build a prompt template from messages with different roles.
        ("system", system_instructions),  # Add the teacher's overall instructions.
        ("human", example_1_question),  # Add the first sample question as a human message.
        ("ai", example_1_answer),  # Add its sample answer as an AI message.
        ("human", example_2_question),  # Add the second sample question.
        ("ai", example_2_answer),  # Add its sample answer.
        ("human", student_request),  # Add the actual student's request template last.
    ])  # Complete the message list and create the prompt template.

    output_parser = StrOutputParser()  # Create a parser that extracts plain text from the model's response.

    chain = prompt | llm | output_parser  # Build the LCEL pipeline: format the prompt, call Gemini, and extract text.

    return chain  # Return the prepared workflow; invoke() or ainvoke() executes it later.