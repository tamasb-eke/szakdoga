# Word game-based comparison of human and machine thinking

This repository contains the code base for the thesis. The following description outlines the structure, operation, and requirements for running the code base.

This work was produced during the course of a diploma thesis in electrical engineering at the Faculty of Electrical Engineering of the Budapest University of Technology and Economics.

## Setup
The program was developed in a linux enviroment. In order to work please consider downloading into a linux enviroment
or use wsl (Windows Subsystem for Linux) alternatively

1. Clone repository:
   ```bash
   git clone https://github.com/tamasb-eke/szakdoga.git
   cd szakdoga
   ```

2. Create a virtual enviroment and activate it:
   ```bash
   python3 -m venv venv
   source ./venv/bin/activate
   ```

3. Install depicencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Get your API keys:  
   If you want to use the Chatbot part of the code, you need to get API 
   key for LLM communication. Please be aware that API usage is usually 
   subject to payment.
   Your API key should be placed into a .env file. (There is an example
   .env file in config_example)

   Google: https://aistudio.google.com/  
   Claude: https://console.anthropic.com  
   ChatGPT: https://platform.openai.com/  

5. Running:
  - If you want to use the development enviroment (for testing):
    ```bash
    APP_ENV=dev ./venv/bin/python ./src/main.py
    ```
  - If you want to use the production enviroment:
    ```bash
    APP_ENV=prod ./venv/bin/python ./src/main.py
    ```

## Project structure
You can see in the example files, how should the .env files look.

```
/szakdoga
│── /data               # Data-related files (database.db)
│   │── game_guides
│── /config             # enviroment variables, secrets, keys
│   │── .env
│   │── dev.env
│   │── prod.env
│── /scr                # Source code folder
│   │── /classes        # Custom-made classes
|   │   │── DAO         # Data Oriented Objects (DAO) for database
│   │── /models         # models for the programs
│   │── /scripts        # Utility functions/helpers
|   │   │── load        # load data to database
|   │   │── chatbot     # LLM API handler
|   │   │── logger      # Custom logger 
|   │   │── terminal    # Custom terminal for repeting tasks
|   │   │── visualize   # Create picture for evaluating
│   │── main.py         # Main script
│── README.md           # Project description
│── requirements.txt    # Dependencies
```

## Licence

This project may only be used for educational and research purposes.  
Any other use requires the prior permission of the author.