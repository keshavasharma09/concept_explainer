# STEP 3: APP.PY
# Create the Chainlit interface and handle settings, user messages, and model responses.


# ---------------------------------------------------------
# PART 1: IMPORT THE REQUIRED LIBRARIES
# ---------------------------------------------------------

import logging  # Record error information in the terminal through Python's logging system.

import chainlit as cl  # Import Chainlit to create and manage the chat interface.

from chainlit.input_widget import Select  # Import the dropdown widget for chat settings.

from explainer import build_chain, ConfigurationError  # Import the chain builder and custom configuration exception.


# ---------------------------------------------------------
# PART 2: CREATE THE APPLICATION LOGGER
# ---------------------------------------------------------

logger = logging.getLogger(__name__)  # Create a logger according to the current Python module.


# ---------------------------------------------------------
# PART 3: PREPARE AND STORE THE EXPLANATION CHAIN
# ---------------------------------------------------------

async def configure_chain():  # Define an asynchronous function that prepares the chain and reports setup errors.

    try:  # Attempt setup and handle exceptions if setup fails.

        chain = build_chain()  # Run the synchronous builder to prepare the prompt, model, and output parser.

        cl.user_session.set("chain", chain)  # Store the prepared chain in the current user's session.

        return chain  # Return the chain if local configuration succeeds; this does not test an API request.

    except ConfigurationError as exc:  # Catch a configuration problem and store the exception in exc.

        cl.user_session.set("chain", None)  # Clear the stored chain because configuration failed.

        await cl.Message(  # Create a message and wait for its send operation to finish.
            content=f"**Configuration issue**\n\n{exc}"  # Display the custom error with a bold heading and blank line.
        ).send()  # Send the configuration error to the chat interface.

    except Exception as exc:  # Catch other ordinary exceptions raised during chain initialization.

        cl.user_session.set("chain", None)  # Clear any previously stored chain after initialization fails.

        error_type = type(exc).__name__  # Extract the exception's class name without including its full message.

        logger.error("Model initialization failed: %s", error_type)  # Log the failure type using deferred string formatting.

        await cl.Message(  # Create a user-facing initialization error message.
            content=(  # Combine the following adjacent strings into one message.
                f"**Model initialization failed: {error_type}**\n\n"  # Show the exception type in a bold heading.
                "Check the installed packages and Gemini model configuration."  # Suggest areas to inspect.
            )  # Complete the message content.
        ).send()  # Send the error message and wait for sending to finish.

    return None  # Indicate that setup failed after either exception handler finishes.


# ---------------------------------------------------------
# PART 4: INITIALIZE A NEW CHAT
# ---------------------------------------------------------

@cl.on_chat_start  # Register the following function to run when a new chat starts.
async def start():  # Define the asynchronous chat-start handler.

    settings = await cl.ChatSettings([  # Create the settings panel and receive its initial selected values.
        Select(  # Create the learning-level dropdown.
            id="level",  # Use "level" as the key for this setting in the returned dictionary.
            label="Learning level",  # Display this label beside the dropdown.
            values=["Beginner", "Intermediate", "Advanced"],  # Define the available learning levels.
            initial_index=0,  # Select the first option, Beginner, by default.
        ),  # Complete the learning-level dropdown.
        Select(  # Create the explanation-language dropdown.
            id="language",  # Use "language" as the key for this setting.
            label="Explanation language",  # Display this label beside the dropdown.
            values=["English", "Hinglish", "Hindi"],  # Define the available response languages.
            initial_index=0,  # Select the first option, English, by default.
        ),  # Complete the language dropdown.
    ]).send()  # Send the settings panel to the interface and wait for the operation to finish.

    cl.user_session.set("settings", settings)  # Store the initial dropdown values in the current session.

    chain = await configure_chain()  # Prepare and store the chain, allowing the helper to report setup errors.

    if chain is None:  # Check whether chain configuration failed.
        return  # Stop this handler without displaying the ready message.

    await cl.Message(  # Create the welcome message after successful local setup.
        content=(  # Combine the following strings into one welcome message.
            "**AI Concept Explainer is ready.**\n\n"  # Display a bold heading followed by a blank line.
            "Choose your learning level and language in chat settings, "  # Explain where to select preferences.
            "then enter a topic.\n\n"  # Ask the user to submit a topic after choosing settings.
            "For example: **What is machine learning?**\n\n"  # Provide an example question with bold formatting.
            "Each request is processed independently."  # Explain that earlier conversation turns are not included.
        )  # Complete the welcome message content.
    ).send()  # Send the welcome message and wait for sending to finish.


# ---------------------------------------------------------
# PART 5: HANDLE CHANGES TO CHAT SETTINGS
# ---------------------------------------------------------

@cl.on_settings_update  # Register the following function to run when chat settings change.
async def update_settings(settings):  # Receive the updated settings dictionary from Chainlit.

    cl.user_session.set("settings", settings)  # Replace the stored settings with the latest selections.


# ---------------------------------------------------------
# PART 6: RECEIVE AND VALIDATE THE USER'S MESSAGE
# ---------------------------------------------------------

@cl.on_message  # Register the following function to run whenever the user submits a message.
async def explain(message: cl.Message):  # Receive the submitted Chainlit Message object; the annotation describes its expected type.

    topic = message.content.strip()  # Read the message text and remove leading and trailing whitespace.

    if not topic:  # Check whether the submitted text is empty after removing whitespace.
        await cl.Message(  # Create a validation message for the user.
            content="Please enter a topic."  # Ask the user to provide a non-empty topic.
        ).send()  # Send the validation message.
        return  # Stop processing this empty request.


# ---------------------------------------------------------
# PART 7: RETRIEVE OR REBUILD THE CHAIN
# ---------------------------------------------------------

    chain = cl.user_session.get("chain")  # Retrieve the chain stored in the current user's session.

    if chain is None:  # Retry setup if no usable chain is currently stored.
        chain = await configure_chain()  # Read the configuration again and attempt to build the chain.

    if chain is None:  # Check whether the retry also failed.
        return  # Stop because the setup helper has already displayed an error.


# ---------------------------------------------------------
# PART 8: RETRIEVE THE USER'S SETTINGS
# ---------------------------------------------------------

    settings = cl.user_session.get("settings") or {  # Use stored settings, or defaults if they are missing or empty.
        "level": "Beginner",  # Use Beginner as the fallback learning level.
        "language": "English",  # Use English as the fallback explanation language.
    }  # Complete the default settings dictionary.


# ---------------------------------------------------------
# PART 9: DISPLAY A PROGRESS MESSAGE
# ---------------------------------------------------------

    reply = cl.Message(content="Generating your explanation...")  # Create a message that will later contain the answer or error.

    await reply.send()  # Display the progress message before starting the model request.


# ---------------------------------------------------------
# PART 10: EXECUTE THE EXPLANATION CHAIN
# ---------------------------------------------------------

    try:  # Attempt to generate and process the explanation.

        answer = await chain.ainvoke({  # Execute the chain asynchronously and wait for its final text result.
            "topic": topic,  # Fill the prompt's topic placeholder with the user's message.
            "level": settings["level"],  # Fill the level placeholder with the selected learning level.
            "language": settings["language"],  # Fill the language placeholder with the selected language.
        })  # Complete the input dictionary and wait for the chain result.

        reply.content = answer.strip() or (  # Remove outer whitespace and use a fallback if the answer is empty.
            "No text was returned. Try rephrasing your topic."  # Provide guidance when the returned text is empty.
        )  # Store the final text in the existing reply object; the interface is updated later.


# ---------------------------------------------------------
# PART 11: HANDLE REQUEST OR RESPONSE-PROCESSING ERRORS
# ---------------------------------------------------------

    except Exception as exc:  # Catch ordinary exceptions raised inside the generation and processing block.

        error_type = type(exc).__name__  # Extract only the exception's class name.

        logger.error("Gemini request failed: %s", error_type)  # Log the failure type without logging the full exception message.

        reply.content = (  # Replace the pending reply content with an error message.
            f"**Gemini request failed: {error_type}**\n\n"  # Show the failure type in a bold heading.
            "Local setup completed, but the model request failed. "  # Explain the failure using the application's message.
            "Check API-key validity, model access, billing, quota, "  # List configuration and account settings to inspect.
            "and your internet connection."  # Include network connectivity as another possible cause.
        )  # Complete the error message.


# ---------------------------------------------------------
# PART 12: UPDATE THE DISPLAYED MESSAGE


    await reply.update()  # Replace the displayed progress message with the answer or error stored in reply.content.