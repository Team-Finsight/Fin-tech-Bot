import streamlit as st
import tempfile
import os
# Interpreter setup
import interpreter
interpreter.api_base = "https://api.endpoints.anyscale.com/v1"
interpreter.api_key = "esecret_fv9yhc2f1ix7lfdztdfh1fd6n8"
interpreter.model = "anyscale/codellama/CodeLlama-34b-Instruct-hf"
interpreter.auto_run = True
import litellm
litellm.set_verbose = False
litellm.add_function_to_prompt = True
interpreter.context_window = 16000
# Set a system message for the interpreter
interpreter.system_message = """Please develop a Python script and execute it for the user input that complies with the following criteria:

1.The script should exclusively utilize Python for all data manipulation tasks.
2.If the document is of type 'xlsx' or 'csv', the script should use the pandas library for processing.
3.Always use raw string literals for file paths. For example, assign a file path to a variable like this: file_path = r'your_file_path_here'.
4.The script should first print the column names of the dataframe.
5.Utilize the printed column names in the subsequent code you generate. always excute full code
6.Ensure the script always prints the top 5 rows of the dataframe to facilitate better understanding of the data.
7.If any part of the script encounters an error, try alternative methods to achieve the desired outcome.
8.The script must be adaptable to various file paths while strictly adhering to these instructions.
9.Focus on providing solutions directly related to the user's query.
10.Conclude the script with the answer to the user's input.
Use this as a guideline to ensure the script meets all the requirements and handles the data as specified."""

# Function to save the uploaded file to a temporary location
def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

def delete_temporary_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
# Initialize session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Page configuration
st.set_page_config(
    page_title="Fin-Tech-Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
subtitle_html = """
    <div style="text-align: center;">
        <h2 style="color: grey; margin-bottom: 25px;">How can I assist you today?🫡</h2>
        <p>Select an option below to have a general chat🗣️, upload a document📃, or perform file manipulations📂.</p>
    </div>
"""

# Title
st.title("💬 Fin-Tech-Bot")
st.markdown(subtitle_html, unsafe_allow_html=True)

# Radio button to choose chat environment
chat_environment = st.radio("Choose chat environment:", ["General Chat", "Chat with Document"])

# Initialize variables
uploaded_file = None
document_path = None

# Handle file upload and text input based on chat environment
if chat_environment == "Chat with Document":
    uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "csv","xlsx","xlsb","xlsm","xls"])
    user_input = st.text_input("Write here your message:")
    if uploaded_file:
        document_path = save_uploaded_file(uploaded_file)
        st.session_state['uploaded_file_path'] = document_path
    else:
    # Check if previously uploaded file has been removed
        if 'uploaded_file_path' in st.session_state and st.session_state['uploaded_file_path'] is not None:
            # Delete the temporary file
            delete_temporary_file(st.session_state['uploaded_file_path'])
            st.session_state['uploaded_file_path'] = None
            interpreter.reset()
if chat_environment == "General Chat":
    prompt = st.text_input("Write here your message:")


# Start Chat button functionality
if st.button("Start Chat"):
    with st.spinner("Performing chat..."):
        if chat_environment == "Chat with Document":
            if document_path:
                # Handle chat with document
                st.text_area("Document Path", document_path)
                prompt = f"Document path: {document_path}\n{interpreter.system_message}\n{user_input}"
            else:
                st.warning("Please upload a document to proceed.")
                prompt = None  # Set prompt to None if no document is uploaded


            with st.chat_message("assistant"):
                codeb = True
                outputb = False
                full_response = ""
                message_placeholder = st.empty()
                for chunk in interpreter.chat(prompt, display=True, stream=True):
            
                    # Message
                    if "message" in chunk:
                        full_response += chunk["message"]
                        if chunk['message'] == ":":
                            full_response += "\n"

                    # Code
                    if "code" in chunk:
                    # Handle code lines
                        if full_response.endswith("```"):
                            if chunk['code'].find("\n")!=-1 and codeb:
                                partido = full_response[:len(full_response)-3].split("```")[-1]
                                full_response = full_response.replace("```"+partido,"\n```\n" + partido + chunk['code'])
                                codeb = False
                            else:
                                full_response = full_response[:len(full_response)-3] + chunk['code'] + "```"
                        else:
                            full_response += f"```{chunk['code']}```"
                        
                        # Output
                        if "executing" in chunk:
                            # Handle code execution messages
                            if full_response.endswith("```") and full_response[:len(full_response)-3].split("```")[-1].find("\n") != -1:
                                full_response = full_response[:len(full_response)-3] + "\n```"
                            full_response += f"\n\n```{chunk['executing']['language']}\n{chunk['executing']['code']}\n```"
                        if "output" in chunk:
                            # Handle output messages
                            if chunk["output"] != "KeyboardInterrupt" and outputb:
                                full_response = full_response[:len(full_response)-4] + chunk['output'] + "\n```\n"
                            elif chunk["output"] != "KeyboardInterrupt":
                                full_response += f"\n\n```text\n{chunk['output']}```\n"
                                outputb = True
                            codeb = True

                        if "end_of_execution" in chunk:
                            # Add a newline to separate executions
                            full_response = full_response.strip()
                            full_response += "\n"

                        # Join the formatted messages
                        # full_response += json.dumps(chunk)
                        message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        elif chat_environment == "General Chat" and prompt:
            # General chat environment
            with st.chat_message("user"):
                st.text(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                codeb = True
                outputb = False
                full_response = ""
                message_placeholder = st.empty()

                # Display the full_response
                message_placeholder = st.empty()
                for chunk in interpreter.chat(prompt, display=True, stream=True):
                    # Message
                    if "message" in chunk:
                        full_response += chunk["message"]
                        if chunk['message'] == ":":
                            full_response += "\n"

                    # Code
                    if "code" in chunk:
                    # Handle code lines
                        if full_response.endswith("```"):
                            if chunk['code'].find("\n")!=-1 and codeb:
                                partido = full_response[:len(full_response)-3].split("```")[-1]
                                full_response = full_response.replace("```"+partido,"\n```\n" + partido + chunk['code'])
                                codeb = False
                            else:
                                full_response = full_response[:len(full_response)-3] + chunk['code'] + "```"
                        else:
                            full_response += f"```{chunk['code']}```"
                        
                        # Output
                        if "executing" in chunk:
                            # Handle code execution messages
                            if full_response.endswith("```") and full_response[:len(full_response)-3].split("```")[-1].find("\n") != -1:
                                full_response = full_response[:len(full_response)-3] + "\n```"
                            full_response += f"\n\n```{chunk['executing']['language']}\n{chunk['executing']['code']}\n```"
                        if "output" in chunk:
                            # Handle output messages
                            if chunk["output"] != "KeyboardInterrupt" and outputb:
                                full_response = full_response[:len(full_response)-4] + chunk['output'] + "\n```\n"
                            elif chunk["output"] != "KeyboardInterrupt":
                                full_response += f"\n\n```text\n{chunk['output']}```\n"
                                outputb = True
                            codeb = True

                        if "end_of_execution" in chunk:
                            # Add a newline to separate executions
                            full_response = full_response.strip()
                            full_response += "\n"
                        message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})


# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message(msg["role"]).text(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message(msg["role"]).markdown(msg["content"])


