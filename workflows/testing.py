"""
Enter script name

Enter short description of the script
"""

__date__ = "2024-12-26"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



# %% --------------------------------------------------------------------------
# Import Modules
from src.chatbot import ChatbotWorkflow
chatbot = ChatbotWorkflow(50024800)

# %%
input_message = ""
while input_message != "Exit":
    input_message = input("Enter your message: ")
    output = chatbot.stream(input_message)
    print(output)

# %%
