"""
Enter script name

Enter short description of the script
"""

__date__ = "2024-12-26"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



# %% --------------------------------------------------------------------------
# Import Modules
from src.chatbot import set_up_chatbot_workflow, chatbot
# Load the workflow
set_up_chatbot_workflow()

# %%
input_message = ""
while input_message != "Exit":
    input_message = input("Enter your message: ")
    output = chatbot(input_message)
    print(output)

# %%
