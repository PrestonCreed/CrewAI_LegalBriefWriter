import os
import logging
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

logging.basicConfig(level=logging.INFO)

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "Your API Key Here"

# File saving function
def save_to_file(content: str, filename: str) -> str:
    try:
        with open(filename, 'w') as file:
            file.write(content)
        return f"Content successfully saved to {filename}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

# Email sending function
def send_email(subject: str, body: str, to_email: str, attachment: str = None) -> str:
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    sender_email = "your email"
    sender_password = "your password"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    if attachment:
        with open(attachment, "rb") as file:
            part = MIMEApplication(file.read(), Name=os.path.basename(attachment))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
        message.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        return "Email sent successfully"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Pydantic models for tool inputs
class FileInput(BaseModel):
    content: str
    filename: str

class EmailInput(BaseModel):
    subject: str
    body: str
    to_email: str
    attachment: str = None

# Create tools
save_tool = StructuredTool.from_function(
    func=save_to_file,
    name="SaveToFile",
    description="Save content to a file",
    args_schema=FileInput
)

send_email_tool = StructuredTool.from_function(
    func=send_email,
    name="SendEmail",
    description="Send an email",
    args_schema=EmailInput
)

# Create agents
legal_writer = Agent(
    role='Legal Brief Writer',
    goal='Write a comprehensive and persuasive legal brief for the bank fraud case',
    backstory='You are an experienced legal writer with expertise in bank fraud cases.',
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(model_name="gpt-4")
)

formatter = Agent(
    role='Document Formatter',
    goal='Format the legal brief according to standard guidelines and save it',
    backstory='You are an expert in legal document formatting.',
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(model_name="gpt-4"),
    tools=[save_tool]
)

email_sender = Agent(
    role='Email Composer and Sender',
    goal='Compose a summary email and send it with the legal brief attached',
    backstory='You are an AI assistant specializing in professional communication.',
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(model_name="gpt-4"),
    tools=[send_email_tool]
)

# Create tasks
write_brief_task = Task(
    description='''Write a comprehensive legal brief for a random case that you will create. 
    Include all necessary sections: Introduction, Statement of Facts, Legal Arguments, Relief Sought, and Conclusion. 
    Provide specific details about the alleged fraudulent activities, relevant laws, and precedents.
    This should be the full, detailed legal brief, not a summary.''',
    agent=legal_writer,
    expected_output="A detailed and persuasive legal brief in text format."
)

format_brief_task = Task(
    description='''Format the legal brief according to standard legal document guidelines. 
    Ensure all sections are properly structured and labeled. 
    Use the SaveToFile tool to save the formatted content as 'Legal_Brief.txt'.
    Confirm that the file has been saved successfully.''',
    agent=formatter,
    expected_output="Confirmation that the fully formatted legal brief has been saved as Legal_Brief.txt."
)

send_email_task = Task(
    description='''Compose a professional email to johndoe@gmail.com. Create the subject based on the case details.
    In the email body, provide a brief introduction and a concise summary of the key points from the legal brief. 
    Do not include the full text of the legal brief in the email body.
    Use the SendEmail tool to send the email, attaching the 'Legal_Brief.txt' file.
    Confirm that the email has been sent successfully.''',
    agent=email_sender,
    expected_output="Confirmation that the email has been sent successfully with the full legal brief attached."
)

# Create crew
legal_brief_crew = Crew(
    agents=[legal_writer, formatter, email_sender],
    tasks=[write_brief_task, format_brief_task, send_email_task],
    process=Process.sequential,
    verbose=True
)

# Run the crew
try:
    result = legal_brief_crew.kickoff()
    print("Final Result:", result)
    
    # Check if the email was sent successfully
    if "email has been sent successfully" in str(result).lower():
        print("Email sent successfully!")
    else:
        print("Warning: Email may not have been sent. Please check the logs.")
        
except Exception as e:
    logging.error(f"An error occurred during execution: {str(e)}")